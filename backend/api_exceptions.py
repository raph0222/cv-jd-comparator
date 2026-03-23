"""
DRF-style API exceptions for Flask: set status_code, default_detail, and default_code
on subclasses, then `raise SomeException` from views or use cases.
"""


class APIException(Exception):
    status_code = 500
    default_detail = "A server error occurred."
    default_code = "error"

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code
        self.detail = str(detail)
        self.code = str(code)
        super().__init__(self.detail)

    def to_error_payload(self) -> dict:
        return {"code": self.code, "message": self.detail}


class BadRequest(APIException):
    status_code = 400
    default_detail = "Bad request."
    default_code = "bad_request"


class UnsupportedMediaType(APIException):
    status_code = 415
    default_detail = "Content-Type must be application/json."
    default_code = "unsupported_media_type"


class InvalidJsonBody(BadRequest):
    default_detail = "Invalid JSON body."
    default_code = "bad_request"


class JobDescriptionTooLong(APIException):
    status_code = 400
    default_detail = "The job description is too long."
    default_code = "job_description_too_long"


class ResumeTooLong(APIException):
    status_code = 400
    default_detail = "The resume is too long."
    default_code = "resume_too_long"


class InternalError(APIException):
    status_code = 500
    default_detail = "Comparison failed due to an internal error."
    default_code = "error"


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = "Service temporarily unavailable, try again later."
    default_code = "service_unavailable"
