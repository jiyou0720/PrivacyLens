from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-5.6-luna"
    openai_review_model: str = "gpt-5.6-terra"
    openai_reasoning_effort: str = "low"
    openai_review_reasoning_effort: str = "low"
    openai_embedding_model: str = "text-embedding-3-small"
    prompt_version: str = "v4-low-latency-review"
    rule_version: str = "consent-rules-v5"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
