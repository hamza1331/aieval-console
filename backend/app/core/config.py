"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "Aieval Console"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Local-first defaults (NFR-09)
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS origins
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Security & resource bounds (NFR-07)
    MAX_PAYLOAD_BYTES: int = 524288  # 500 KB

    # API Documentation toggle (FR-15, NFR-15)
    ENABLE_OPENAPI: bool = True

    # Database configuration (Phase 2)
    DATABASE_URL: str = "sqlite:///./data/aieval.db"


settings = Settings()
