import uuid

from flask import Blueprint, jsonify, request

from backend.api_exceptions import InvalidJsonBody, UnsupportedMediaType
from backend.application.use_cases.compare_cv import run_compare
from backend.extensions import limiter
from backend.infrastructure.config.settings import get_settings
from backend.infrastructure.observability.context import set_request_id

compare_bp = Blueprint("compare", __name__, url_prefix="/api/v1")


@compare_bp.route("/compare", methods=["POST"])
@limiter.limit(
    lambda: get_settings().rate_limit,
    exempt_when=lambda: not get_settings().rate_limit,
)
def compare():
    if not request.is_json:
        raise UnsupportedMediaType()

    payload = request.get_json(silent=True)
    if payload is None:
        raise InvalidJsonBody()

    client_ip = request.remote_addr or "unknown"
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    set_request_id(request_id)

    data = run_compare(payload, client_ip=client_ip, request_id=request_id)
    response = jsonify({"data": data})
    response.status_code = 200
    response.headers["X-Request-ID"] = request_id
    return response
