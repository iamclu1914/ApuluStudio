from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    # Application
    app_name: str = "Apulu Studio"
    debug: bool = False
    secret_key: str

    # Encryption (for OAuth tokens)
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    encryption_key: str | None = None

    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    database_url: str

    # Database SSL Configuration
    # Options: disable, allow, prefer, require, verify-ca, verify-full
    # Production should use 'verify-full' for maximum security
    # Development can use 'require' or 'disable' for local databases
    database_ssl_mode: Literal["disable", "allow", "prefer", "require", "verify-ca", "verify-full"] = "require"
    # Path to CA certificate file (required for verify-ca and verify-full modes)
    database_ssl_ca_cert: str | None = None

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # AI
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ai_provider: Literal["openai", "anthropic"] = "openai"

    # Meta (Instagram, Facebook, Threads)
    meta_app_id: str | None = None
    meta_app_secret: str | None = None
    meta_access_token: str | None = None
    ig_user_id: str | None = None
    fb_page_id: str | None = None
    threads_user_id: str | None = None

    # Bluesky
    bluesky_handle: str | None = None
    bluesky_app_password: str | None = None

    # LinkedIn
    linkedin_client_id: str | None = None
    linkedin_client_secret: str | None = None

    # X (Twitter)
    x_api_key: str | None = None
    x_api_secret: str | None = None
    x_access_token: str | None = None
    x_access_secret: str | None = None

    # LATE API (for Instagram, Threads, TikTok)
    # Get your API key from https://getlate.dev
    late_api_key: str | None = None
    late_sync_interval_seconds: int = 300
    late_sync_user_id: str | None = None

    # URLs
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    # Auto-convert DATABASE_URL schemes for compatibility
    # Render and Supabase may provide postgres:// or postgresql://
    # but SQLAlchemy async needs postgresql+asyncpg://
    @model_validator(mode="after")
    def fix_database_url(self) -> "Settings":
        url = self.database_url
        if url.startswith("postgres://"):
            self.database_url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            self.database_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
