from functools import lru_cache
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file, not the working directory.
# This means uvicorn can be launched from any directory and will always
# find the correct .env sitting next to the backend/ folder.
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",           # Don't error on unrecognized .env entries
    )

    # ── Database ──────────────────────────────────────────────────
    DATABASE_URL: str

    # ── JWT ───────────────────────────────────────────────────────
    SECRET_KEY: str               # Required — no default; must be set in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                "Generate one with: "
                "python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
