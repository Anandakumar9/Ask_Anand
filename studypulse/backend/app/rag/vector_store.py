"""Qdrant vector store for semantic question search with FastEmbed.

Provides:
  - Semantic search: find questions similar to a topic description
  - Deduplication: detect when a generated question is too similar to an existing one
  - Filtered search: narrow results by exam / subject / topic via payload indexes

Embedding runs in a thread-pool (CPU-bound ONNX) so it never blocks the event loop.
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_embed_pool = ThreadPoolExecutor(max_workers=2)


class QuestionVectorStore:
    """Manages question vectors in Qdrant."""

    _instance: Optional["QuestionVectorStore"] = None

    def __init__(self):
        self._client = None
        self._embedding_model = None
        self._collection = settings.QDRANT_COLLECTION
        self._available = False

    @classmethod
    def get_instance(cls) -> "QuestionVectorStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Lifecycle ─────────────────────────────────────────────

    async def initialize(self):
        """Connect to Qdrant, create collection, load embedding model."""
        try:
            from qdrant_client import AsyncQdrantClient, models as qm

            self._client = AsyncQdrantClient(
                host=settings.QDRANT_HOST, port=settings.QDRANT_PORT
            )

            # Ensure collection exists
            cols = await self._client.get_collections()
            if not any(c.name == self._collection for c in cols.collections):
                await self._client.create_collection(
                    collection_name=self._collection,
                    vectors_config=qm.VectorParams(
                        size=settings.EMBEDDING_DIM,
                        distance=qm.Distance.COSINE,
                    ),
                )
                for field in ["exam_id", "subject_id", "topic_id"]:
                    await self._client.create_payload_index(
                        collection_name=self._collection,
                        field_name=field,
                        field_schema=qm.PayloadSchemaType.INTEGER,
                    )
                await self._client.create_payload_index(
                    collection_name=self._collection,
                    field_name="is_previous_year",
                    field_schema=qm.PayloadSchemaType.BOOL,
                )
                logger.info(f"Created Qdrant collection '{self._collection}'")

            # Load embedding model in thread pool (first load ~2s)
            loop = asyncio.get_event_loop()
            self._embedding_model = await loop.run_in_executor(
                _embed_pool, self._load_model
            )

            self._available = True
            logger.info(
                f"Vector store ready: {self._collection} / {settings.EMBEDDING_MODEL}"
            )
        except Exception as e:
            logger.warning(f"Vector store init failed: {e}. Running without semantic search.")
            self._available = False

    @staticmethod
    def _load_model():
        from fastembed import TextEmbedding

        return TextEmbedding(model_name=settings.EMBEDDING_MODEL)

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    # ── Embedding helper ──────────────────────────────────────

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        if not self._embedding_model:
            return []
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _embed_pool,
            lambda: [e.tolist() for e in self._embedding_model.embed(texts)],
        )

    # ── Index questions ───────────────────────────────────────

    async def add_questions(self, questions: list[dict]) -> int:
        """Index questions into Qdrant.

        Each dict must have: id, question_text, options,
        and optionally: exam_id, subject_id, topic_id, difficulty, is_previous_year
        """
        if not self._available or not questions:
            return 0
        try:
            from qdrant_client import models as qm

            texts = []
            for q in questions:
                opts = q.get("options", {})
                opt_str = (
                    " ".join(f"{k}: {v}" for k, v in opts.items())
                    if isinstance(opts, dict)
                    else str(opts)
                )
                texts.append(f"{q['question_text']} {opt_str}")

            vecs = await self._embed(texts)
            if not vecs:
                return 0

            points = [
                qm.PointStruct(
                    id=q["id"],
                    vector=vecs[i],
                    payload={
                        "question_text": q.get("question_text", ""),
                        "options": q.get("options", {}),
                        "correct_answer": q.get("correct_answer", ""),
                        "explanation": q.get("explanation", ""),
                        "exam_id": q.get("exam_id", 0),
                        "subject_id": q.get("subject_id", 0),
                        "topic_id": q.get("topic_id", 0),
                        "difficulty": q.get("difficulty", "medium"),
                        "is_previous_year": q.get("is_previous_year", False),
                    },
                )
                for i, q in enumerate(questions)
            ]
            await self._client.upsert(collection_name=self._collection, points=points)
            logger.info(f"Indexed {len(points)} questions in Qdrant")
            return len(points)
        except Exception as e:
            logger.error(f"Failed to index questions: {e}")
            return 0

    # ── Semantic search ───────────────────────────────────────

    async def search_similar(
        self,
        query_text: str,
        topic_id: Optional[int] = None,
        exam_id: Optional[int] = None,
        exclude_ids: Optional[list[int]] = None,
        limit: int = 20,
        score_threshold: float = 0.3,
    ) -> list[dict]:
        """Find semantically similar questions, with optional metadata filtering."""
        if not self._available:
            return []
        try:
            from qdrant_client import models as qm

            vecs = await self._embed([query_text])
            if not vecs:
                return []

            must, must_not = [], []
            if topic_id is not None:
                must.append(
                    qm.FieldCondition(key="topic_id", match=qm.MatchValue(value=topic_id))
                )
            if exam_id is not None:
                must.append(
                    qm.FieldCondition(key="exam_id", match=qm.MatchValue(value=exam_id))
                )
            if exclude_ids:
                must_not.append(qm.HasIdCondition(has_id=exclude_ids))

            qf = None
            if must or must_not:
                qf = qm.Filter(
                    must=must or None, must_not=must_not or None
                )

            hits = await self._client.query_points(
                collection_name=self._collection,
                query=vecs[0],
                query_filter=qf,
                limit=limit,
                score_threshold=score_threshold,
            )
            return [{**h.payload, "id": h.id, "score": h.score} for h in hits.points]
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def find_duplicates(
        self, question_text: str, threshold: float = None
    ) -> list[dict]:
        """Find questions that are semantically near-duplicates."""
        threshold = threshold or settings.SIMILARITY_DEDUP_THRESHOLD
        return await self.search_similar(
            query_text=question_text, limit=5, score_threshold=threshold
        )


# Singleton
vector_store = QuestionVectorStore.get_instance()
