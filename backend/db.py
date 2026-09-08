import os
from typing import Generator, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

ENV = os.getenv("ENVIRONMENT") or os.getenv("FASTAPI_ENV") or "development"
TESTING = os.getenv("TESTING", "0") == "1" or ENV == "test"


def resolve_database_uri(raw: Optional[str] = None) -> str:
    """Normalize a Postgres URL for SQLAlchemy, including Neon/Railway values."""
    uri = raw
    if uri is None:
        uri = os.getenv("DATABASE_URI") or os.getenv("DATABASE_URL")
    if not uri:
        defaults = {
            "development": "postgresql://postgres:postgres@localhost:5432/quizness",
            "test": "postgresql://postgres:postgres@localhost:5432/quizness_test",
        }
        uri = defaults.get(ENV, defaults["development"])

    uri = uri.replace("postgres://", "postgresql://", 1)

    needs_ssl = "neon.tech" in uri or ENV == "production"
    if needs_ssl and "sslmode=" not in uri:
        separator = "&" if "?" in uri else "?"
        uri = f"{uri}{separator}sslmode=require"

    return uri


DATABASE_URI = resolve_database_uri()

engine: Engine = None
SessionLocal = None


def get_engine() -> Engine:
    """Get database engine with lazy initialization."""
    global engine
    if engine is None:
        uri = resolve_database_uri()
        print("Initializing database connection")

        connect_args = {}
        if uri.startswith("postgresql"):
            connect_args["connect_timeout"] = 5

        engine = create_engine(
            uri,
            pool_timeout=30,
            pool_recycle=300,
            pool_pre_ping=True,
            connect_args=connect_args,
            echo=False,
        )

    return engine


def get_session_local():
    """Get SessionLocal with lazy initialization."""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine()
        )
    return SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# For backwards compatibility and testing
def reset_db_connection():
    """Reset database connection (useful for testing)."""
    global engine, SessionLocal
    if engine:
        engine.dispose()
    engine = None
    SessionLocal = None
