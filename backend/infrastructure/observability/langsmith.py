import logging
import os

from backend.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


def configure_langsmith(settings: Settings) -> None:
    """Configure LangSmith tracing via environment variables.

    LangChain's LangSmith integration reads its config exclusively from
    ``os.environ``.  There is no programmatic API to configure it otherwise,
    so we *must* write these env vars at startup.
    """
    if not settings.langsmith_tracing:
        os.environ["LANGSMITH_TRACING"] = "false"
        return

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    if settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    logger.info("LangSmith tracing enabled project=%s endpoint=%s", settings.langsmith_project, settings.langsmith_endpoint)
