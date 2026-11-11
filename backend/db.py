"""Engine and session wiring.

The engine is built lazily so importing the app (for tests, or for `--help`)
never requires a reachable database.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        url = get_settings().database_url
        if not url:
            raise RuntimeError(
                "DATABASE_URL is not set. See .env.example for the three "
                "Supabase connection-string forms."
            )
        _engine = create_engine(
            url,
            pool_pre_ping=True,  # silently replaces connections the pooler dropped
            pool_size=5,
            max_overflow=5,
            future=True,
        )
        _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False, class_=Session)
    return _engine


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a session per request."""
    get_engine()
    assert _SessionLocal is not None
    with _SessionLocal() as session:
        yield session
