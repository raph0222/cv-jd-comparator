import logging
from typing import Any, Dict

from backend.infrastructure.config.settings import get_settings
from backend.infrastructure.observability.tracing import trace_span
from backend.llm.factory import get_llm_provider, get_model_name
from backend.schemas.api_models import CompareRequest, CompareResponse, ModelSelection
from backend.application.pipeline import run_match_pipeline

logger = logging.getLogger(__name__)


def run_compare(payload: Any, client_ip: str = "unknown", request_id: str = "") -> Dict[str, Any]:
    """Execute the compare use case.

    Returns the response dict on success.
    Raises ValueError for validation errors; other exceptions propagate.
    """
    settings = get_settings()
    with trace_span("run_compare", request_id=request_id):
        compare_request = CompareRequest.from_payload(
            payload, max_input_length=settings.max_input_length,
        )

        logger.info(
            "request_id=%s compare_received client_ip=%s job_description_len=%d resume_len=%d",
            request_id,
            client_ip,
            len(compare_request.job_description),
            len(compare_request.resume),
        )

        selected_models = ModelSelection.from_mapping(
            {
                "provider": get_llm_provider(),
                "model": get_model_name(),
            }
        )
        pipeline_result = run_match_pipeline(
            model=selected_models.model,
            job_description=compare_request.job_description,
            resume=compare_request.resume,
        )
        pipeline_result["request_id"] = request_id

        response = CompareResponse.from_pipeline_result(
            result=pipeline_result,
            models=selected_models,
        )

        return response.to_dict()
