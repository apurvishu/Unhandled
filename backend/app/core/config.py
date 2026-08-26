"""
Application configuration using Pydantic Settings.

All configuration is loaded from environment variables or .env file.
"""

from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== Application =====
    APP_NAME: str = "SIH26006 Freight Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # ===== Database =====
    POSTGRES_USER: str = "sih26006"
    POSTGRES_PASSWORD: str = "changeme_in_production"
    POSTGRES_DB: str = "sih26006"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+psycopg2://sih26006:changeme_in_production@localhost:5432/sih26006"
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://sih26006:changeme_in_production@localhost:5432/sih26006"

    # ===== Redis =====
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://localhost:6379/0"

    # ===== JWT =====
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ===== CORS =====
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ===== External APIs =====
    AIS_API_KEY: str = ""
    AIS_API_URL: str = ""
    WEATHER_API_KEY: str = ""
    WEATHER_API_URL: str = ""
    FREIGHT_API_KEY: str = ""
    FREIGHT_API_URL: str = ""

    # ===== Celery =====
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ===== ML =====
    ML_MODELS_DIR: str = "data/models"
    FREIGHT_MODEL_VERSION: str = "v1.0"
    CONGESTION_MODEL_VERSION: str = "v1.0"

    # ===== Logging =====
    LOG_LEVEL: str = "INFO"


# Singleton settings instance
settings = Settings()
