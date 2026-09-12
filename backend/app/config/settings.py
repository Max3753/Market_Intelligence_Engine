"""Application settings loaded from environment / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the MIE backend.

    All values can be overridden via environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Infrastructure ---
    DATABASE_URL: str = (
        "postgresql+asyncpg://mie:mie@localhost:5432/mie"
    )
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- LLM ---
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "deepseek-chat"

    # --- Crawling ---
    CRAWL_INTERVAL_MINUTES: int = 60

    # --- Environment ---
    ENV: str = "development"

    # --- Github ---
    GITHUB_TOKEN: str = ""

    # --- Zhihu ---
    ZHIHU_COOKIES: str = ""

settings = Settings()
