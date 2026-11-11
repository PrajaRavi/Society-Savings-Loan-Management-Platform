"""Core configuration and settings, harmonized with backend/config/settings.py."""
import json
import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Import existing settings and API keys from backend/config/settings.py if available
try:
    from config import settings as legacy_settings
    _DEFAULT_DATABASE_URL = getattr(legacy_settings, "DATABASE_URL", None)
    _DEFAULT_SUPABASE_URL = getattr(legacy_settings, "SUPABASE_URL", "")
    _DEFAULT_SUPABASE_KEY = getattr(legacy_settings, "SUPABASE_KEY", "")
    _DEFAULT_REDIS_URL = getattr(legacy_settings, "REDIS_URL", "redis://localhost:6379/0")
except ImportError:
    try:
        from backend.config import settings as legacy_settings
        _DEFAULT_DATABASE_URL = getattr(legacy_settings, "DATABASE_URL", None)
        _DEFAULT_SUPABASE_URL = getattr(legacy_settings, "SUPABASE_URL", "")
        _DEFAULT_SUPABASE_KEY = getattr(legacy_settings, "SUPABASE_KEY", "")
        _DEFAULT_REDIS_URL = getattr(legacy_settings, "REDIS_URL", "redis://localhost:6379/0")
    except ImportError:
        _DEFAULT_DATABASE_URL = None
        _DEFAULT_SUPABASE_URL = ""
        _DEFAULT_SUPABASE_KEY = ""
        _DEFAULT_REDIS_URL = "redis://localhost:6379/0"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Society Savings & Loan Management"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"

    # Database URLs
    # Accepts raw postgresql:// from settings/env and exposes both async and sync URLs
    DATABASE_URL: str = (
        _DEFAULT_DATABASE_URL
        or os.getenv("DATABASE_URL")
        or "postgresql://postgres:postgres@localhost:5432/postgres"
    )
    SYNC_DATABASE_URL: str = (
        os.getenv("SYNC_DATABASE_URL")
        or _DEFAULT_DATABASE_URL
        or "postgresql://postgres:postgres@localhost:5432/postgres"
    )

    # Supabase API Credentials
    SUPABASE_URL: str = (
        os.getenv("SUPABASE_URL")
        or _DEFAULT_SUPABASE_URL
    )
    SUPABASE_SERVICE_KEY: str = (
        os.getenv("SUPABASE_SERVICE_KEY")
        or _DEFAULT_SUPABASE_KEY
    )

    # Database Pool & Resilience Settings
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_MAX_RETRIES: int = 5
    DB_RETRY_BASE_DELAY: float = 1.0
    DB_RETRY_MAX_DELAY: float = 16.0

    # Celery & Redis
    REDIS_URL: str = (
        os.getenv("REDIS_URL")
        or _DEFAULT_REDIS_URL
    )
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Auth & Security
    AUTH_MODE: str = "dummy"
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @property
    def async_database_url(self) -> str:
        """Returns the PostgreSQL connection string formatted for asyncpg driver."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """Returns the PostgreSQL connection string formatted for sync driver (psycopg2/default)."""
        url = self.SYNC_DATABASE_URL
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return url

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if not v.startswith("["):
                return [i.strip() for i in v.split(",") if i.strip()]
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except Exception:
                pass
        elif isinstance(v, list):
            return [str(item) for item in v]
        return [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
