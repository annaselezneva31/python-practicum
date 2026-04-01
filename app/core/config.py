from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="FACT_", env_file_encoding="utf-8"
    )

    app_name: str = "Fact Aggregator"
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/facts"
    redis_url: str = "redis://redis:6379"
    celery_broker_url: str = "redis://redis:6379"
    celery_result_backend: str = "redis://redis:6379"
    fetch_interval_seconds: int = 20
    external_fact_api: str = (
        "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
