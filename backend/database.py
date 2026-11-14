"""Database engine & session management for EzyHelpers CHAP.

Supports dual-mode persistence:
1. Neon Serverless PostgreSQL (Production): High-performance pooled connection
   over SSL (`postgresql+psycopg://` with `sslmode=require`).
2. SQLite (Local fallback): Embedded fallback database (`chap_crm.db`) so local
   demos and developer offline testing never crash if cloud credentials are absent.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

# Normalize connection string protocol for psycopg 3
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)


def _make_engine(url: str):
    """Creates a SQLAlchemy engine configured for the database dialect."""
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    # Pool pre-ping ensures dead or idle serverless connections are safely recycled
    return create_engine(url, pool_pre_ping=True)


def _build():
    """Initializes primary PostgreSQL engine or gracefully falls back to SQLite."""
    if DATABASE_URL:
        try:
            eng = _make_engine(DATABASE_URL)
            with eng.connect():
                pass
            return eng, DATABASE_URL
        except Exception as exc:  # noqa: BLE001
            print(f"[db] PostgreSQL connection notice ({exc.__class__.__name__}); falling back to local SQLite")
    url = "sqlite:///./chap_crm.db"
    return _make_engine(url), url


# Active database engine and URL tracking
engine, ACTIVE_URL = _build()

# Thread-safe database session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Declarative Base class for all SQLAlchemy ORM models."""
    pass


def get_db():
    """FastAPI Dependency: Yields an isolated database session and guarantees cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
