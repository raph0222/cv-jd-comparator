"""
Qdrant vector store service for the "Find Best Candidates" feature.

Two collections are kept separate: ``resumes`` and ``job_descriptions``. Documents
are chunked, embedded with a fastembed (ONNX) model and upserted as points
whose payload carries the parent document id (``resume_id`` / ``jd_id``) and the
``chunk_index`` so the parent text can be fetched back from SQLite.

Heavy dependencies (``qdrant-client``, ``fastembed``) are imported
lazily inside methods so that importing this module never breaks the existing
Compare feature when those packages are not installed. The client and the
embedding model are built once per process (singleton via ``get_qdrant_service``)
and the model/collections are loaded lazily on first use.
"""
import logging
import threading
import uuid
from functools import lru_cache
from typing import List

from backend.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

RESUMES_COLLECTION = "resumes"
JOB_DESCRIPTIONS_COLLECTION = "job_descriptions"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 embedding dimension

# Word-based approximation of the recommended 500-token chunks / 50-token overlap.
CHUNK_SIZE_WORDS = 350
CHUNK_OVERLAP_WORDS = 35


def _chunk_text(content: str) -> List[str]:
    """Split text into overlapping word windows. Always returns at least one chunk."""
    words = content.split()
    if not words:
        return [content.strip()] if content.strip() else []
    if len(words) <= CHUNK_SIZE_WORDS:
        return [" ".join(words)]

    chunks: List[str] = []
    step = CHUNK_SIZE_WORDS - CHUNK_OVERLAP_WORDS
    for start in range(0, len(words), step):
        window = words[start : start + CHUNK_SIZE_WORDS]
        if window:
            chunks.append(" ".join(window))
        if start + CHUNK_SIZE_WORDS >= len(words):
            break
    return chunks


class QdrantService:
    def __init__(self) -> None:
        settings = get_settings()
        self._host = settings.qdrant_host
        self._port = settings.qdrant_port
        self._embedding_model_name = settings.embedding_model
        self._client = None
        self._model = None
        self._collections_ready = False
        self._lock = threading.Lock()

    # --- lazy resources --------------------------------------------------

    def _get_client(self):
        if self._client is None:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(host=self._host, port=self._port)
            logger.info("Qdrant client connected to %s:%s", self._host, self._port)
        return self._client

    def _get_model(self):
        if self._model is None:
            from fastembed import TextEmbedding

            logger.info("Loading embedding model '%s'", self._embedding_model_name)
            self._model = TextEmbedding(model_name=self._embedding_model_name)
        return self._model

    def _ensure_collections(self) -> None:
        if self._collections_ready:
            return
        with self._lock:
            if self._collections_ready:
                return
            from qdrant_client.models import Distance, VectorParams

            client = self._get_client()
            existing = {c.name for c in client.get_collections().collections}
            for name in (RESUMES_COLLECTION, JOB_DESCRIPTIONS_COLLECTION):
                if name not in existing:
                    client.create_collection(
                        collection_name=name,
                        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
                    )
                    logger.info("Created Qdrant collection '%s'", name)
            self._collections_ready = True

    def _embed(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        # fastembed.embed returns a generator of numpy arrays. We rank with cosine
        # distance, which is scale-invariant, so no explicit normalization is needed.
        return [vector.tolist() for vector in model.embed(texts)]

    # --- ingestion -------------------------------------------------------

    def _embed_document(self, collection: str, parent_key: str, parent_id: str, content: str) -> List[str]:
        from qdrant_client.models import PointStruct

        self._ensure_collections()
        chunks = _chunk_text(content)
        if not chunks:
            return []

        vectors = self._embed(chunks)
        chunk_ids = [str(uuid.uuid4()) for _ in chunks]
        points = [
            PointStruct(
                id=chunk_ids[i],
                vector=vectors[i],
                payload={parent_key: parent_id, "chunk_index": i},
            )
            for i in range(len(chunks))
        ]
        self._get_client().upsert(collection_name=collection, points=points)
        logger.info("Embedded %d chunk(s) for %s=%s", len(chunks), parent_key, parent_id)
        return chunk_ids

    def embed_resume(self, resume_id: str, content: str) -> List[str]:
        return self._embed_document(RESUMES_COLLECTION, "resume_id", resume_id, content)

    def embed_job_description(self, jd_id: str, content: str) -> List[str]:
        return self._embed_document(JOB_DESCRIPTIONS_COLLECTION, "jd_id", jd_id, content)

    # --- retrieval -------------------------------------------------------

    def find_similar_resumes(self, jd_content: str, top_k: int = 5) -> List[str]:
        """Return up to ``top_k`` distinct resume ids most similar to the JD.

        The JD is embedded as a single vector; resume chunks are searched and the
        best score per parent resume is kept, then ranked descending.
        """
        self._ensure_collections()
        query_vector = self._embed([jd_content])[0]
        # Over-fetch: a single resume can own several chunks; we need enough hits
        # to surface top_k *distinct* resumes.
        hits = self._get_client().query_points(
            collection_name=RESUMES_COLLECTION,
            query=query_vector,
            limit=max(top_k * 4, top_k),
            with_payload=True,
        ).points

        best_score: dict = {}
        for hit in hits:
            payload = hit.payload or {}
            resume_id = payload.get("resume_id")
            if not resume_id:
                continue
            if resume_id not in best_score or hit.score > best_score[resume_id]:
                best_score[resume_id] = hit.score

        ranked = sorted(best_score.items(), key=lambda kv: kv[1], reverse=True)
        return [resume_id for resume_id, _ in ranked[:top_k]]

    # --- deletion --------------------------------------------------------

    def _delete_chunks(self, collection: str, chunk_ids: List[str]) -> None:
        if not chunk_ids:
            return
        from qdrant_client.models import PointIdsList

        self._get_client().delete(
            collection_name=collection,
            points_selector=PointIdsList(points=list(chunk_ids)),
        )
        logger.info("Deleted %d chunk(s) from '%s'", len(chunk_ids), collection)

    def delete_resume(self, chunk_ids: List[str]) -> None:
        self._delete_chunks(RESUMES_COLLECTION, chunk_ids)

    def delete_job_description(self, chunk_ids: List[str]) -> None:
        self._delete_chunks(JOB_DESCRIPTIONS_COLLECTION, chunk_ids)


@lru_cache(maxsize=1)
def get_qdrant_service() -> QdrantService:
    return QdrantService()


def reset_qdrant_service() -> None:
    """Clear cached service. Intended for test teardown."""
    get_qdrant_service.cache_clear()
