import logging
import uuid
from typing import Any, Dict

from backend.api_exceptions import BadRequest, JobDescriptionTooLong
from backend.infrastructure.config.settings import get_settings
from backend.infrastructure.database.db import get_db
from backend.infrastructure.observability.tracing import trace_span
from backend.infrastructure.rag.qdrant_service import get_qdrant_service

logger = logging.getLogger(__name__)


def ingest_job_description(payload: Any, request_id: str = "") -> Dict[str, Any]:
    """Persist a job description in SQLite and embed it in Qdrant.

    Returns ``{"jd_id": ..., "title": ..., "chunk_count": ...}``.
    Raises APIException subclasses on validation errors.
    """
    settings = get_settings()
    with trace_span("ingest_job_description", request_id=request_id):
        if not isinstance(payload, dict):
            raise BadRequest(detail="Request body must be a JSON object.")

        content = str(payload.get("content") or "").strip()
        title = str(payload.get("title") or "").strip()
        if not content:
            raise BadRequest(detail="job description content is required")
        if not title:
            raise BadRequest(detail="job description title is required")
        if len(content) > settings.max_input_length:
            raise JobDescriptionTooLong()

        jd_id = str(uuid.uuid4())
        chunk_ids = get_qdrant_service().embed_job_description(jd_id=jd_id, content=content)
        get_db().insert_job_description(title, content, chunk_ids, jd_id=jd_id)

        logger.info(
            "request_id=%s job_description_ingested jd_id=%s chunks=%d",
            request_id,
            jd_id,
            len(chunk_ids),
        )
        return {
            "jd_id": jd_id,
            "title": title,
            "chunk_count": len(chunk_ids),
        }
