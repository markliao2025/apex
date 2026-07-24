"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings


DEMO_JWT_SECRET = "apex-demo-only-change-me"


class Settings(BaseSettings):
    """Strongly-typed settings backed by environment variables / .env file."""

    # PostgreSQL
    POSTGRES_USER: str = "apex"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "apex_rigor"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # A full URL takes precedence over the component fields.
    DATABASE_URL: str = ""

    # JWT / Auth
    JWT_SECRET: str = DEMO_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI / LLM
    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: Literal["none", "openai", "compatible", "local"] = "none"

    # API base URLs
    API_BASE_URL: str = "http://localhost:8000"
    VITE_API_BASE_URL: str = "http://localhost:8000"

    # App
    APP_NAME: str = "Apex"
    APP_ENV: Literal["demo", "development", "test", "production"] = "development"
    DEMO_MODE: bool = False
    CONJUNCTION_DEMO_ENABLED: bool = False
    ALLOW_NETWORK_SEED: bool = False
    DEBUG: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @model_validator(mode="after")
    def validate_runtime(self) -> "Settings":
        """Build local defaults and reject unsafe production combinations."""
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )

        if self.APP_ENV == "production":
            unsafe = []
            if self.JWT_SECRET == DEMO_JWT_SECRET or not self.JWT_SECRET:
                unsafe.append("JWT_SECRET must be a non-default value")
            if self.DEMO_MODE:
                unsafe.append("DEMO_MODE must be false")
            if not self.POSTGRES_PASSWORD and self.DATABASE_URL.startswith(
                "postgresql"
            ):
                unsafe.append("POSTGRES_PASSWORD must be non-empty")
            if self.DEBUG:
                unsafe.append("DEBUG must be false")
            if unsafe:
                raise ValueError(
                    "Unsafe production configuration: " + "; ".join(unsafe)
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Because ``functools.lru_cache`` is used, this function returns the same
    object across the entire process lifetime — ideal for dependency injection.
    """
    return Settings()
