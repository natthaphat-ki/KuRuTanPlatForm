"""Application configuration loaded from environment variables (.env).

Follows Phase 0 / Phase 2 requirement: single source of runtime configuration
shared by the FastAPI Core, so Development / Testing / Production only differ
by environment values, never by code.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "KuRuTan V2 API"
    ENVIRONMENT: str = "development"  # development | testing | production
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = (
        "postgresql+psycopg://kurutan:kurutan@localhost:5432/kurutan"
    )

    # --- Auth / Security ---
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # 12 hours

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # --- Embedding / pgvector (foundation for Phase 6) ---
    EMBEDDING_DIMENSION: int = 1536

    # --- Evidence storage (Phase 3 — local disk backend) ---
    STORAGE_DIR: str = "storage"
    MAX_EVIDENCE_FILE_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
