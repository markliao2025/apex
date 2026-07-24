"""Runtime configuration must fail closed in production."""

import pytest
from pydantic import ValidationError

from app.core.config import DEMO_JWT_SECRET, Settings


def test_demo_defaults_are_explicitly_non_production() -> None:
    settings = Settings(
        _env_file=None,
        APP_ENV="demo",
        DEMO_MODE=True,
        CONJUNCTION_DEMO_ENABLED=True,
    )
    assert settings.JWT_SECRET == DEMO_JWT_SECRET


def test_production_rejects_demo_secret_and_mode() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            APP_ENV="production",
            DEMO_MODE=True,
            JWT_SECRET=DEMO_JWT_SECRET,
            DATABASE_URL="postgresql://apex:@db/apex",
        )


def test_full_database_url_takes_precedence() -> None:
    settings = Settings(
        _env_file=None,
        APP_ENV="test",
        DATABASE_URL="sqlite:///:memory:",
    )
    assert settings.DATABASE_URL == "sqlite:///:memory:"
