"""Async Ollama LLM client using httpx — fully non-blocking.

Replaces the old synchronous `requests`-based client that blocked
the FastAPI event loop for 30-60 seconds per generation call.
"""
import json
import logging
import re
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Async client for Ollama LLM inference."""

    _instance: Optional["OllamaClient"] = None

    def __init__(self):
        self._base_url = settings.OLLAMA_BASE_URL
        self._model = settings.OLLAMA_MODEL
        self._timeout = settings.OLLAMA_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_instance(cls) -> "OllamaClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self):
        """Create the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(self._timeout, connect=10.0),
            )
            logger.info(f"Ollama async client ready: {self._base_url} model={self._model}")

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def is_available(self) -> bool:
        """Check if Ollama is running and the model is loaded."""
        try:
            if not self._client:
                await self.initialize()
            resp = await self._client.get("/api/tags")
            if resp.status_code != 200:
                return False
            models = [m.get("name", "") for m in resp.json().get("models", [])]
            model_base = self._model.split(":")[0]
            available = any(model_base in m for m in models)
            if not available:
                logger.warning(f"Model '{self._model}' not found. Available: {models}")
            return available
        except Exception as e:
            logger.warning(f"Ollama not reachable: {e}")
            return False

    async def generate(
        self, prompt: str, system: str = "", temperature: float = 0.7
    ) -> str:
        """Generate a text completion — async, non-blocking."""
        if not self._client:
            await self.initialize()
        try:
            resp = await self._client.post(
                "/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": 4096,
                        "top_p": 0.9,
                    },
                },
            )
            resp.raise_for_status()
            return resp.json().get("response", "")
        except httpx.TimeoutException:
            logger.error(f"Ollama timed out after {self._timeout}s")
            return ""
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return ""

    async def generate_json(
        self, prompt: str, system: str = "", temperature: float = 0.3
    ) -> list | dict | None:
        """Generate and parse JSON. Uses lower temperature for determinism."""
        raw = await self.generate(prompt, system, temperature)
        if not raw:
            return None
        return self._extract_json(raw)

    # ── JSON extraction ───────────────────────────────────────

    @staticmethod
    def _extract_json(text: str) -> list | dict | None:
        """Extract JSON from LLM output, handling code fences and noise."""
        # Try 1: direct parse
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        # Try 2: markdown code block
        for pattern in [r"```json\s*\n?(.*?)\n?\s*```", r"```\s*\n?(.*?)\n?\s*```"]:
            m = re.search(pattern, text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1).strip())
                except json.JSONDecodeError:
                    continue
        # Try 3: find first [ or { and match closing bracket
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
                            return json.loads(text[si : i + 1])
                        except json.JSONDecodeError:
                            break
        logger.warning(f"Could not extract JSON from response ({len(text)} chars)")
        return None


# Singleton
ollama_client = OllamaClient.get_instance()
