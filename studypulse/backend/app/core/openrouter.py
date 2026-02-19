"""OpenRouter API client with multi-LLM fallback for cost optimization.

Supports multiple cheap LLMs with automatic fallback:
- Primary: DeepSeek R1 (ultra-cheap, good quality)
- Fallback 1: Qwen 2.5 (cheap, fast)
- Fallback 2: Llama 3.1 (moderate cost, reliable)
- Fallback 3: GPT-4o-mini (backup, still cheap)

Cost optimization:
- Tracks token usage per model
- Prefers cheaper models first
- Falls back only on errors (not quality)
"""
import json
import logging
import re
from typing import Optional, List, Dict, Any
from enum import Enum

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers via OpenRouter."""
    DEEPSEEK_R1 = "deepseek/deepseek-r1:free"  # Free tier, excellent quality
    DEEPSEEK_CHAT = "deepseek/deepseek-chat"  # Ultra-cheap ($0.14/$0.28 per 1M tokens)
    QWEN_25 = "qwen/qwen-2.5-72b-instruct"  # Very cheap, fast
    LLAMA_31 = "meta-llama/llama-3.1-70b-instruct"  # Moderate cost, reliable
    GPT4O_MINI = "openai/gpt-4o-mini"  # Backup, still cheap ($0.15/$0.60 per 1M tokens)
    
    # Cost per 1M tokens (input/output) - approximate
    COSTS = {
        "deepseek/deepseek-r1:free": (0.0, 0.0),  # Free tier
        "deepseek/deepseek-chat": (0.14, 0.28),
        "qwen/qwen-2.5-72b-instruct": (0.55, 0.55),
        "meta-llama/llama-3.1-70b-instruct": (0.59, 0.79),
        "openai/gpt-4o-mini": (0.15, 0.60),
    }


class OpenRouterClient:
    """Async client for OpenRouter API with multi-LLM fallback."""

    _instance: Optional["OpenRouterClient"] = None
    _base_url = "https://openrouter.ai/api/v1"

    def __init__(self):
        self._api_key = settings.OPENROUTER_API_KEY
        self._client: Optional[httpx.AsyncClient] = None
        self._available = False
        
        # Cost tracking
        self._token_usage: Dict[str, Dict[str, int]] = {}  # model -> {input_tokens, output_tokens}
        self._total_cost = 0.0
        
        # Model priority (cheapest first)
        self._model_priority = [
            LLMProvider.DEEPSEEK_R1,
            LLMProvider.DEEPSEEK_CHAT,
            LLMProvider.QWEN_25,
            LLMProvider.LLAMA_31,
            LLMProvider.GPT4O_MINI,
        ]

    @classmethod
    def get_instance(cls) -> "OpenRouterClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self):
        """Initialize HTTP client."""
        if not self._api_key:
            logger.warning("OpenRouter API key not set - OpenRouter client unavailable")
            self._available = False
            return

        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(60.0, connect=10.0),
                limits=httpx.Limits(
                    max_connections=10,
                    max_keepalive_connections=5,
                ),
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "HTTP-Referer": "https://studypulse.app",  # Optional: for analytics
                    "X-Title": "StudyPulse RAG",
                },
            )
            self._available = True
            logger.info("OpenRouter client initialized")

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def is_available(self) -> bool:
        """Check if OpenRouter is configured and available."""
        if not self._api_key:
            return False
        if not self._client:
            await self.initialize()
        return self._available

    async def generate_json(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_retries: int = 3,
    ) -> Optional[List[Dict] | Dict]:
        """Generate JSON using OpenRouter with automatic fallback.

        Tries models in cost order (cheapest first), falls back on errors.
        
        Returns:
            Parsed JSON (list or dict) or None on failure
        """
        if not await self.is_available():
            logger.warning("OpenRouter not available")
            return None

        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        # Try each model in priority order
        last_error = None
        for model_enum in self._model_priority:
            model_name = model_enum.value
            
            for attempt in range(max_retries):
                try:
                    result = await self._call_api(
                        model=model_name,
                        prompt=full_prompt,
                        temperature=temperature,
                    )
                    
                    if result:
                        # Track usage
                        self._track_usage(model_name, result.get("usage", {}))
                        return self._extract_json(result.get("choices", [{}])[0].get("message", {}).get("content", ""))
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:  # Rate limit
                        logger.warning(f"Rate limited on {model_name}, trying next model...")
                        last_error = e
                        break  # Try next model
                    elif e.response.status_code >= 500:  # Server error
                        logger.warning(f"Server error on {model_name}: {e}, trying next model...")
                        last_error = e
                        break  # Try next model
                    else:
                        logger.error(f"API error on {model_name}: {e}")
                        last_error = e
                        if attempt == max_retries - 1:
                            break  # Try next model
                except Exception as e:
                    logger.error(f"Error calling {model_name}: {e}")
                    last_error = e
                    if attempt == max_retries - 1:
                        break  # Try next model

        logger.error(f"All OpenRouter models failed. Last error: {last_error}")
        return None

    async def _call_api(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.3,
    ) -> Optional[Dict[str, Any]]:
        """Make API call to OpenRouter."""
        if not self._client:
            await self.initialize()

        response = await self._client.post(
            "/chat/completions",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "temperature": temperature,
                "max_tokens": 4096,
                "response_format": {"type": "json_object"},  # Force JSON output
            },
        )
        response.raise_for_status()
        return response.json()

    def _track_usage(self, model: str, usage: Dict[str, int]):
        """Track token usage and cost."""
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        if model not in self._token_usage:
            self._token_usage[model] = {"input_tokens": 0, "output_tokens": 0}
        
        self._token_usage[model]["input_tokens"] += input_tokens
        self._token_usage[model]["output_tokens"] += output_tokens
        
        # Calculate cost
        if model in LLMProvider.COSTS:
            input_cost, output_cost = LLMProvider.COSTS[model]
            cost = (input_tokens / 1_000_000) * input_cost + (output_tokens / 1_000_000) * output_cost
            self._total_cost += cost

    @staticmethod
    def _extract_json(text: str) -> Optional[List[Dict] | Dict]:
        """Extract JSON from LLM response (similar to Ollama's extractor)."""
        text = text.strip()

        # Try 1: direct parse
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "questions" in parsed:
                return parsed["questions"]
            return parsed
        except json.JSONDecodeError:
            pass

        # Try 2: markdown code blocks
        for pattern in [
            r"```json\s*\n?(.*?)\n?\s*```",
            r"```\s*\n?(.*?)\n?\s*```",
        ]:
            m = re.search(pattern, text, re.DOTALL)
            if m:
                try:
                    parsed = json.loads(m.group(1).strip())
                    if isinstance(parsed, dict) and "questions" in parsed:
                        return parsed["questions"]
                    return parsed
                except json.JSONDecodeError:
                    continue

        # Try 3: bracket matching
        for sc, ec in [("[", "]"), ("{", "}")]:
            si = text.find(sc)
            if si == -1:
                continue
            depth = 0
            for i in range(si, len(text)):
                if text[i] == sc:
                    depth += 1
                elif text[i] == ec:
                    depth -= 1
                    if depth == 0:
                        try:
                            parsed = json.loads(text[si : i + 1])
                            if isinstance(parsed, dict) and "questions" in parsed:
                                return parsed["questions"]
                            return parsed
                        except json.JSONDecodeError:
                            break

        logger.warning(f"Could not extract JSON from OpenRouter response: {text[:200]}...")
        return None

    def get_metrics(self) -> Dict[str, Any]:
        """Get usage metrics and cost tracking."""
        return {
            "total_cost_usd": round(self._total_cost, 4),
            "token_usage": self._token_usage.copy(),
            "available": self._available,
        }

    def reset_metrics(self):
        """Reset cost tracking (useful for testing)."""
        self._token_usage = {}
        self._total_cost = 0.0


# Singleton
openrouter_client = OpenRouterClient.get_instance()
