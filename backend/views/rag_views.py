import uuid

from flask import Blueprint, jsonify, request

from backend.api_exceptions import InvalidJsonBody, NotFound, UnsupportedMediaType
from backend.application.use_cases.find_best_candidates import find_best_candidates
from backend.application.use_cases.ingest_job_description import ingest_job_description
from backend.application.use_cases.ingest_resume import ingest_resume
from backend.extensions import limiter
from backend.infrastructure.config.settings import get_settings
from backend.infrastructure.database.db import get_db
from backend.infrastructure.observability.context import set_request_id
from backend.infrastructure.rag.qdrant_service import get_qdrant_service

rag_bp = Blueprint("rag", __name__, url_prefix="/api/v1")


def _begin_request() -> str:
    """Resolve and register the request id, mirroring compare_view."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    set_request_id(request_id)
    return request_id


def _json_body() -> dict:
    if not request.is_json:
        raise UnsupportedMediaType()
    payload = request.get_json(silent=True)
    if payload is None:
        raise InvalidJsonBody()
    return payload


def _respond(data: dict, request_id: str, status_code: int = 200):
    response = jsonify({"data": data})
    response.status_code = status_code
    response.headers["X-Request-ID"] = request_id
    return response


# --- resumes -------------------------------------------------------------


@rag_bp.route("/resumes", methods=["POST"])
def create_resume():
    request_id = _begin_request()
    payload = _json_body()
    data = ingest_resume(payload, request_id=request_id)
    return _respond(data, request_id, status_code=201)


@rag_bp.route("/resumes", methods=["GET"])
def list_resumes():
    request_id = _begin_request()
    data = {"resumes": get_db().list_resumes()}
    return _respond(data, request_id)


@rag_bp.route("/resumes/<resume_id>", methods=["DELETE"])
def delete_resume(resume_id: str):
    request_id = _begin_request()
    resume = get_db().get_resume(resume_id)
    if resume is None:
        raise NotFound(detail="Resume not found.")
    get_qdrant_service().delete_resume(resume.get("chunk_ids") or [])
    get_db().delete_resume(resume_id)
    return _respond({"resume_id": resume_id, "deleted": True}, request_id)


# --- job descriptions ----------------------------------------------------


@rag_bp.route("/job-descriptions", methods=["POST"])
def create_job_description():
    request_id = _begin_request()
    payload = _json_body()
    data = ingest_job_description(payload, request_id=request_id)
    return _respond(data, request_id, status_code=201)


@rag_bp.route("/job-descriptions", methods=["GET"])
def list_job_descriptions():
    request_id = _begin_request()
    data = {"job_descriptions": get_db().list_job_descriptions()}
    return _respond(data, request_id)


@rag_bp.route("/job-descriptions/<jd_id>", methods=["DELETE"])
def delete_job_description(jd_id: str):
    request_id = _begin_request()
    jd = get_db().get_job_description(jd_id)
    if jd is None:
        raise NotFound(detail="Job description not found.")
    get_qdrant_service().delete_job_description(jd.get("chunk_ids") or [])
    get_db().delete_job_description(jd_id)
    return _respond({"jd_id": jd_id, "deleted": True}, request_id)


# --- main feature --------------------------------------------------------


@rag_bp.route("/job-descriptions/<jd_id>/find-candidates", methods=["POST"])
@limiter.limit(
    lambda: get_settings().rate_limit,
    exempt_when=lambda: not get_settings().rate_limit,
)
def find_candidates(jd_id: str):
    request_id = _begin_request()
    data = find_best_candidates(jd_id, request_id=request_id)
    return _respond(data, request_id)
