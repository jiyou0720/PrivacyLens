from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PRIVACYLENS_", env_file=".env")

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:0.6b"
    ollama_timeout_seconds: float = 120
    prompt_version: str = "consent-extraction-v1"
    rule_version: str = "consent-rules-v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
