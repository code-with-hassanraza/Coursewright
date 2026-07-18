"""
backend/app/core/config.py
Coursewright — Application Settings

All environment variables are read here via pydantic-settings.
No other file in the backend should read os.environ directly.

Usage (anywhere in the backend or AI service):
    from app.core.config import settings

    db_url   = settings.DATABASE_URL
    ai_key   = settings.GEMINI_API_KEY

In development: values are loaded from backend/.env
In production:  values are injected as real env vars
                (populated from AWS Secrets Manager at EC2 startup)
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ------------------------------------------------------------------
    # DATABASE
    # Required. No default — app must fail loudly if this is missing.
    # Format: postgresql://user:password@host:5432/dbname
    # ------------------------------------------------------------------
    DATABASE_URL: str

    # ------------------------------------------------------------------
    # JWT
    # SECRET_KEY: Required. Generate with:
    #   python -c "import secrets; print(secrets.token_hex(32))"
    # ALGORITHM:  HS256 is the standard symmetric JWT algorithm.
    # EXPIRE:     60 minutes is a reasonable session length.
    # ------------------------------------------------------------------
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ------------------------------------------------------------------
    # APPLICATION
    # ENVIRONMENT:     Controls behaviour differences between dev and prod.
    #                  Checked in logging.py and main.py.
    # ALLOWED_ORIGINS: Comma-separated list of allowed CORS origins.
    #                  The CORS middleware in main.py splits on ",".
    #                  Default covers the Vite dev server.
    # ------------------------------------------------------------------
    ENVIRONMENT: str = "development"             # development | production
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # ------------------------------------------------------------------
    # SEED ACCOUNT
    # Created at first startup by the backend's startup event handler.
    # Defaults to empty string — seeding is skipped if these are blank.
    # ------------------------------------------------------------------
    FIRST_ADMIN_EMAIL: str = ""
    FIRST_ADMIN_PASSWORD: str = ""

    # ------------------------------------------------------------------
    # AI API KEYS
    # Read by the AI teammate's services in backend/app/services/.
    # Default to empty string so the app starts even if not yet set.
    # The AI service layer must handle the empty-string case gracefully.
    # ------------------------------------------------------------------
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # ------------------------------------------------------------------
    # PYDANTIC-SETTINGS CONFIG
    # env_file:      Reads from backend/.env in development.
    #                Ignored in production (real env vars take precedence).
    # case_sensitive: Required on Linux (EC2/Docker) where env var names
    #                 are case-sensitive. DATABASE_URL ≠ database_url.
    # ------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Returns the Settings singleton.
    lru_cache ensures .env is parsed exactly once per process lifetime.
    Call get_settings() if you need to clear the cache in tests:
        get_settings.cache_clear()
    """
    return Settings()


# Module-level singleton — this is what everything imports.
# Importing this module triggers Settings() once, then caches it.
settings = get_settings()