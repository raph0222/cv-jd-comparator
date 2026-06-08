import logging
import uuid
from typing import Any, Dict

from backend.api_exceptions import BadRequest, ResumeTooLong
from backend.infrastructure.config.settings import get_settings
from backend.infrastructure.database.db import get_db
from backend.infrastructure.observability.tracing import trace_span
from backend.infrastructure.rag.qdrant_service import get_qdrant_service

logger = logging.getLogger(__name__)


def ingest_resume(payload: Any, request_id: str = "") -> Dict[str, Any]:
    """Persist a resume in SQLite and embed it in Qdrant.

    Returns ``{"resume_id": ..., "candidate_name": ..., "chunk_count": ...}``.
    Raises APIException subclasses on validation errors.
    """
    settings = get_settings()
    with trace_span("ingest_resume", request_id=request_id):
        if not isinstance(payload, dict):
            raise BadRequest(detail="Request body must be a JSON object.")

        content = str(payload.get("content") or "").strip()
        candidate_name = str(payload.get("candidate_name") or "").strip()
        if not content:
            raise BadRequest(detail="resume content is required")
        if len(content) > settings.max_input_length:
            raise ResumeTooLong()

        resume_id = str(uuid.uuid4())
        chunk_ids = get_qdrant_service().embed_resume(resume_id=resume_id, content=content)
        get_db().insert_resume(candidate_name, content, chunk_ids, resume_id=resume_id)

        logger.info(
            "request_id=%s resume_ingested resume_id=%s chunks=%d",
            request_id,
            resume_id,
            len(chunk_ids),
        )
        return {
            "resume_id": resume_id,
            "candidate_name": candidate_name,
            "chunk_count": len(chunk_ids),
        }
