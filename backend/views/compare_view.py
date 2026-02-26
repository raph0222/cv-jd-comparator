import logging
import uuid

from flask import Blueprint, jsonify, request

from backend.application.use_cases.compare_cv import run_compare
from backend.extensions import limiter
from backend.infrastructure.config.settings import get_settings
from backend.infrastructure.observability.context import set_request_id
from backend.schemas.api_models import ErrorResponse

logger = logging.getLogger(__name__)

compare_bp = Blueprint("compare", __name__, url_prefix="/api/v1")


@compare_bp.route("/compare", methods=["POST"])
@limiter.limit(
    lambda: get_settings().rate_limit,
    exempt_when=lambda: not get_settings().rate_limit,
)
def compare():
    if not request.is_json:
        body = {"error": ErrorResponse(code="unsupported_media_type", message="Content-Type must be application/json").to_dict()}
        return jsonify(body), 415

    payload = request.get_json(silent=True)
    if payload is None:
        body = {"error": ErrorResponse(code="bad_request", message="Invalid JSON body").to_dict()}
        return jsonify(body), 400

    client_ip = request.remote_addr or "unknown"
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    set_request_id(request_id)

    try:
        data = run_compare(payload, client_ip=client_ip, request_id=request_id)
        response = jsonify({"data": data})
        response.status_code = 200
    except ValueError as exc:
        logger.warning("request_id=%s validation_error message=%s", request_id, str(exc))
        body = {"error": ErrorResponse(code="bad_request", message=str(exc)).to_dict()}
        response = jsonify(body)
        response.status_code = 400
    except Exception:
        logger.exception("request_id=%s unexpected_error during /api/v1/compare", request_id)
        body = {"error": ErrorResponse(code="internal_error", message="Comparison failed due to an internal error.").to_dict()}
        response = jsonify(body)
        response.status_code = 500

    response.headers["X-Request-ID"] = request_id
    return response
