from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import DatabaseConfig


_engine = None
_SessionLocal = None


def create_app_engine():
    config = DatabaseConfig.from_env()
    return create_engine(config.sqlalchemy_url(), pool_pre_ping=True, future=True)


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_app_engine()
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _SessionLocal


def SessionLocal() -> Session:
    return get_session_factory()()


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
