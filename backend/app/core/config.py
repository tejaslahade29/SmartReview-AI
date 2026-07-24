from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "AI Contract Review Platform"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5434/contract_review"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: list[str] = ["http://localhost:3001"]

    LOG_LEVEL: str = "INFO"

    DOCUMENT_STORAGE_DIR: str = "./storage/documents"
    MAX_UPLOAD_SIZE_MB: int = 25

    # Which AI provider the Review Engine calls by default. Both providers'
    # settings can be configured at once (e.g. to keep a paid Claude key
    # ready while running on Gemini's free tier day-to-day) — this flag
    # just picks which one is actually used.
    AI_PROVIDER: str = "gemini"

    ANTHROPIC_API_KEY: str | None = None
    CLAUDE_MODEL: str = "claude-opus-4-8"
    CLAUDE_MAX_TOKENS: int = 8000
    CLAUDE_TIMEOUT_SECONDS: float = 120.0
    CLAUDE_MAX_RETRIES: int = 2

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_MAX_OUTPUT_TOKENS: int = 8000
    GEMINI_TIMEOUT_SECONDS: float = 120.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
