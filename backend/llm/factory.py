import logging

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_vertexai import ChatVertexAI
from langchain_ollama import ChatOllama
from backend.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

PROVIDER_OLLAMA = "ollama"
PROVIDER_GEMINI_VERTEX = "gemini-vertex"

def get_llm_provider() -> str:
    settings = get_settings()
    provider = settings.llm_provider
    valid = {PROVIDER_OLLAMA, PROVIDER_GEMINI_VERTEX}
    if provider not in valid:
        msgError = "Unsupported LLM_PROVIDER value. Use one of: "
        msgError += ", ".join(valid)
        raise ValueError(msgError)
    return provider


def get_model_name() -> str:
    """Return active model name from settings (defaults set in settings)."""
    return get_settings().llm_model


def get_chat_model(model_name: str, temperature: float) -> BaseChatModel:
    """
    Build a LangChain chat model configured from environment.
    """
    settings = get_settings()
    provider = get_llm_provider()

    if provider == PROVIDER_GEMINI_VERTEX:
        if not settings.google_cloud_project:
            raise ValueError("Missing GOOGLE_CLOUD_PROJECT for gemini-vertex provider.")
        logger.info(
            "Using gemini model '%s' via Vertex AI (%s, %s).",
            model_name,
            settings.google_cloud_project,
            settings.google_cloud_location,
        )
        return ChatVertexAI(
            model=model_name,
            temperature=temperature,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )

    # Ollama path (local Docker service by default).
    base_url = settings.llm_base_url
    logger.info("Using ollama model '%s' via endpoint %s", model_name, base_url)
    return ChatOllama(
        model=model_name,
        temperature=temperature,
        base_url=base_url,
    )
