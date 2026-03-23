import logging
import uuid

from flask import jsonify, request
from flask_limiter.errors import RateLimitExceeded
from backend.api_exceptions import APIException

logger = logging.getLogger(__name__)


def register_error_handlers(flask_app):
    """Central JSON error responses (similar idea to DRF EXCEPTION_HANDLER)."""

    @flask_app.errorhandler(APIException)
    def handle_api_exception(exc: APIException):
        from backend.infrastructure.observability.context import get_request_id

        request_id = get_request_id() or request.headers.get("X-Request-ID") or str(uuid.uuid4())
        body = {"error": exc.to_error_payload()}
        response = jsonify(body)
        response.status_code = exc.status_code
        response.headers["X-Request-ID"] = request_id
        return response

    @flask_app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(_exc: RateLimitExceeded):
        from backend.infrastructure.observability.context import get_request_id

        request_id = get_request_id() or request.headers.get("X-Request-ID") or str(uuid.uuid4())
        body = {
            "error": {
                "code": "rate_limit_exceeded",
                "message": "Too many requests. Please wait and try again.",
            }
        }
        response = jsonify(body)
        response.status_code = 429
        response.headers["X-Request-ID"] = request_id
        return response

    @flask_app.errorhandler(Exception)
    def handle_unexpected_exception(_exc: Exception):
        """Last resort: avoid leaking internals; log and return generic code ``error``."""
        from backend.infrastructure.observability.context import get_request_id

        request_id = get_request_id() or request.headers.get("X-Request-ID") or str(uuid.uuid4())
        logger.exception("request_id=%s unhandled_exception", request_id)
        body = {
            "error": {
                "code": "error",
                "message": "An unexpected error occurred.",
            }
        }
        response = jsonify(body)
        response.status_code = 500
        response.headers["X-Request-ID"] = request_id
        return response
