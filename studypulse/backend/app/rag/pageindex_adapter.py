"""PageIndex Adapter - Lightweight vector store using hnswlib.

This is a drop-in replacement for Qdrant, designed for embedded deployments.
Uses hnswlib (HNSW algorithm) for fast approximate nearest neighbor search.

Benefits over Qdrant:
- No separate server needed (embedded/in-process)
- Lower memory footprint (~20-50 MB vs 200-500 MB)
- Faster initialization (~0.5s vs ~3s)
- Simpler deployment (just pip install)
- Perfect for <100k vectors

Trade-offs:
- No built-in payload filtering (we filter in Python)
- Less scalable than Qdrant (good for 10-100k vectors)
- Manual persistence management
"""
import asyncio
import json
import logging
import pickle
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, List, Dict

import hnswlib
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

_embed_pool = ThreadPoolExecutor(max_workers=2)


class PageIndexStore:
    """Lightweight vector store using hnswlib - drop-in replacement for Qdrant."""

    _instance: Optional["PageIndexStore"] = None

    def __init__(self):
        self._index: Optional[hnswlib.Index] = None
        self._embedding_model = None
        self._metadata: Dict[int, dict] = {}  # id → full metadata
        self._current_count = 0
        self._max_elements = 100000  # Maximum vectors (can be increased)
        self._available = False
        self._storage_path = Path(settings.PAGEINDEX_STORAGE_PATH)
        self._storage_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_instance(cls) -> "PageIndexStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Lifecycle ─────────────────────────────────────────────

    async def initialize(self):
        """Initialize hnswlib index and embedding model."""
        try:
            # Initialize HNSW index
            self._index = hnswlib.Index(
                space="cosine",  # Cosine similarity (same as Qdrant)
                dim=settings.EMBEDDING_DIM  # 384 for BAAI/bge-small-en-v1.5
            )

            # Try to load existing index
            index_file = self._storage_path / "index.bin"
            metadata_file = self._storage_path / "metadata.pkl"

            if index_file.exists() and metadata_file.exists():
                logger.info("Loading existing PageIndex from disk...")
                self._index.load_index(str(index_file))
                with open(metadata_file, 'rb') as f:
                    self._metadata = pickle.load(f)
                self._current_count = len(self._metadata)
                logger.info(f"Loaded {self._current_count} vectors from PageIndex")
            else:
                # Initialize new index
                logger.info("Initializing new PageIndex...")
                self._index.init_index(
                    max_elements=self._max_elements,
                    ef_construction=200,  # Higher = better quality, slower build
                    M=16  # Number of connections per layer
                )
                self._current_count = 0

            # Set query parameters
            self._index.set_ef(50)  # Higher = better recall, slower search

            # Load embedding model (same as Qdrant: FastEmbed)
            loop = asyncio.get_event_loop()
            self._embedding_model = await loop.run_in_executor(
                _embed_pool, self._load_model
            )

            self._available = True
            logger.info(
                f"PageIndex ready: {self._current_count} vectors, "
                f"model={settings.EMBEDDING_MODEL}"
            )

        except Exception as e:
            logger.warning(f"PageIndex init failed: {e}. Running without semantic search.")
            self._available = False

    @staticmethod
    def _load_model():
        """Load FastEmbed model in thread pool (CPU-bound ONNX)."""
        from fastembed import TextEmbedding
        return TextEmbedding(model_name=settings.EMBEDDING_MODEL)

    async def close(self):
        """Save index and clean up resources."""
        if self._index and self._available:
            await self._save()
        self._index = None
        self._available = False

    async def _save(self):
        """Save index and metadata to disk."""
        try:
            index_file = self._storage_path / "index.bin"
            metadata_file = self._storage_path / "metadata.pkl"

            # Save HNSW index
            self._index.save_index(str(index_file))

            # Save metadata
            with open(metadata_file, 'wb') as f:
                pickle.dump(self._metadata, f)

            logger.info(f"Saved PageIndex ({self._current_count} vectors)")
        except Exception as e:
            logger.error(f"Failed to save PageIndex: {e}")

    @property
    def available(self) -> bool:
        return self._available

    # ── Embedding helper ──────────────────────────────────────

    async def _embed(self, texts: List[str]) -> List[List[float]]:
        """Embed texts using FastEmbed model (runs in thread pool)."""
        if not self._embedding_model:
            return []
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _embed_pool,
            lambda: [e.tolist() for e in self._embedding_model.embed(texts)],
        )

    # ── Index questions ───────────────────────────────────────

    async def add_questions(self, questions: List[dict]) -> int:
        """Index questions into PageIndex.

        Each dict must have: id, question_text, options,
        and optionally: exam_id, subject_id, topic_id, difficulty, is_previous_year
        """
        if not self._available or not questions:
            return 0

        try:
            # Prepare texts for embedding
            texts = []
            for q in questions:
                opts = q.get("options", {})
                opt_str = (
                    " ".join(f"{k}: {v}" for k, v in opts.items())
                    if isinstance(opts, dict)
                    else str(opts)
                )
                texts.append(f"{q['question_text']} {opt_str}")

            # Embed texts
            vectors = await self._embed(texts)
            if not vectors:
                return 0

            # Prepare data for hnswlib
            ids = np.array([q["id"] for q in questions], dtype=np.int64)
            vectors_np = np.array(vectors, dtype=np.float32)

            # Resize index if needed
            if self._current_count + len(questions) > self._max_elements:
                new_max = self._max_elements * 2
                logger.info(f"Resizing PageIndex: {self._max_elements} → {new_max}")
                self._index.resize_index(new_max)
                self._max_elements = new_max

            # Add to index
            self._index.add_items(vectors_np, ids)

            # Store metadata
            for i, q in enumerate(questions):
                self._metadata[q["id"]] = {
                    "question_text": q.get("question_text", ""),
                    "options": q.get("options", {}),
                    "correct_answer": q.get("correct_answer", ""),
                    "explanation": q.get("explanation", ""),
                    "exam_id": q.get("exam_id", 0),
                    "subject_id": q.get("subject_id", 0),
                    "topic_id": q.get("topic_id", 0),
                    "difficulty": q.get("difficulty", "medium"),
                    "is_previous_year": q.get("is_previous_year", False),
                }

            self._current_count += len(questions)

            # Save to disk (async)
            await self._save()

            logger.info(f"Indexed {len(questions)} questions in PageIndex (total: {self._current_count})")
            return len(questions)

        except Exception as e:
            logger.error(f"Failed to index questions: {e}")
            return 0

    # ── Semantic search ───────────────────────────────────────

    async def search_similar(
        self,
        query_text: str,
        topic_id: Optional[int] = None,
        exam_id: Optional[int] = None,
        exclude_ids: Optional[List[int]] = None,
        limit: int = 20,
        score_threshold: float = 0.3,
    ) -> List[dict]:
        """Find semantically similar questions with metadata filtering.

        Note: Unlike Qdrant's built-in payload filtering, we do post-filtering
        in Python. This means we fetch more candidates and filter them.
        """
        if not self._available or not self._index:
            return []

        try:
            # Embed query
            vectors = await self._embed([query_text])
            if not vectors:
                return []

            query_vector = np.array(vectors[0], dtype=np.float32)

            # Search (fetch more candidates for filtering)
            # Rule of thumb: fetch 5x limit to account for filtering
            k = min(limit * 5, self._current_count)
            if k == 0:
                return []

            labels, distances = self._index.knn_query(query_vector, k=k)

            # Convert distances to cosine similarity scores
            # hnswlib returns L2 distances for cosine space
            # Score = 1 - (distance^2 / 2)
            scores = 1 - (distances[0] ** 2 / 2)

            # Build results
            results = []
            exclude_set = set(exclude_ids) if exclude_ids else set()

            for idx, (label, score) in enumerate(zip(labels[0], scores)):
                # Skip if below threshold
                if score < score_threshold:
                    continue

                # Skip if excluded
                if label in exclude_set:
                    continue

                # Get metadata
                meta = self._metadata.get(label)
                if not meta:
                    continue

                # Filter by topic_id
                if topic_id is not None and meta.get("topic_id") != topic_id:
                    continue

                # Filter by exam_id
                if exam_id is not None and meta.get("exam_id") != exam_id:
                    continue

                # Add to results
                results.append({
                    **meta,
                    "id": int(label),
                    "score": float(score)
                })

                # Stop when we have enough
                if len(results) >= limit:
                    break

            return results

        except Exception as e:
            logger.error(f"PageIndex search failed: {e}")
            return []

    async def find_duplicates(
        self, question_text: str, threshold: float = None
    ) -> List[dict]:
        """Find questions that are semantically near-duplicates."""
        threshold = threshold or settings.SIMILARITY_DEDUP_THRESHOLD
        return await self.search_similar(
            query_text=question_text, limit=5, score_threshold=threshold
        )


# Singleton instance
pageindex_store = PageIndexStore.get_instance()
