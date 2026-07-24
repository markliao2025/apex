"""SQLAlchemy engine and session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # verify connections before use
    pool_recycle=3600,  # recycle after 1 hour to avoid stale connections
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    """FastAPI dependency that yields a database session.

    The session is automatically closed (rolled back) when the request ends.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
