import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional


@dataclass(frozen=True)
class Settings:
    app_env: str
    log_level: str
    structured_logs: bool
    langsmith_tracing: bool
    langsmith_project: str
    langsmith_api_key: str
    langsmith_endpoint: str
    cors_allowed_origins: List[str]
    llm_provider: str
    llm_base_url: str
    llm_model: str
    google_cloud_project: str
    google_cloud_location: str
    max_input_length: int
    rate_limit: str

    @classmethod
    def from_env(cls) -> "Settings":
        cors_raw = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:9919,http://127.0.0.1:9919")

        return cls(
            app_env=os.environ.get("APP_ENV", "development"),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            structured_logs=os.environ.get("STRUCTURED_LOGS", "false"),
            langsmith_tracing=os.environ.get("LANGSMITH_TRACING", "false"),
            langsmith_project=os.environ.get("LANGSMITH_PROJECT", ""),
            langsmith_api_key=os.environ.get("LANGSMITH_API_KEY", ""),
            langsmith_endpoint=os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
            cors_allowed_origins=[o.strip() for o in cors_raw.split(",") if o.strip()], # accepts multiple origins separated by commas
            llm_provider=os.environ.get("LLM_PROVIDER", "ollama"),
            llm_base_url=os.environ.get("LLM_BASE_URL", "http://llm:11434"),
            llm_model=os.environ.get("LLM_MODEL", "qwen2.5:3b"),
            google_cloud_project=os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
            google_cloud_location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
            max_input_length=int(os.environ.get("MAX_INPUT_LENGTH") or "50000"),
            rate_limit=os.environ.get("RATE_LIMIT", ""),
        )

    @property
    def cors_origins_for_flask(self):
        if "*" in self.cors_allowed_origins:
            return "*"
        return self.cors_allowed_origins


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()


def reset_settings() -> None:
    """Clear cached settings. Intended for test teardown."""
    get_settings.cache_clear()
