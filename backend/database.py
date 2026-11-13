import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)


def _make_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True)


def _build():
    """Use Postgres when reachable; otherwise fall back to SQLite so demos never crash."""
    if DATABASE_URL:
        try:
            eng = _make_engine(DATABASE_URL)
            with eng.connect():
                pass
            return eng, DATABASE_URL
        except Exception as exc:  # noqa: BLE001
            print(f"[db] Postgres unavailable ({exc.__class__.__name__}); falling back to SQLite")
    url = "sqlite:///./chap_crm.db"
    return _make_engine(url), url


engine, ACTIVE_URL = _build()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

