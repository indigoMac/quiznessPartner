import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

# Get environment (default to development)
ENV = os.getenv("FASTAPI_ENV", "development")

# Check if we're in testing mode
TESTING = os.getenv("TESTING", "0") == "1" or os.getenv("ENVIRONMENT") == "test"

# Database URIs for different environments
DATABASE_URLS = {
    # Use Docker PostgreSQL for development
    "development": "postgresql://postgres:postgres@localhost:5432/quizness",
    # Use PostgreSQL for tests (will be overridden by conftest.py anyway)
    "test": "postgresql://postgres:postgres@localhost:5432/quizness_test",
    "production": os.getenv("DATABASE_URL"),  # For production (e.g., Heroku)
}

# Get the appropriate database URL
DATABASE_URI = os.getenv("DATABASE_URI", DATABASE_URLS[ENV])

# For Heroku PostgreSQL which uses DATABASE_URL
if os.getenv("DATABASE_URL"):
    DATABASE_URI = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://")

# Global variables for lazy initialization
engine: Engine = None
SessionLocal = None


def get_engine() -> Engine:
    """Get database engine with lazy initialization."""
    global engine
    if engine is None:
        print(f"Initializing database connection: {DATABASE_URI}")

        if TESTING:
            # For PostgreSQL in CI/testing, add connection timeout and pooling
            connect_args = {}
            if DATABASE_URI.startswith("postgresql"):
                connect_args = {"connect_timeout": 5}

            engine = create_engine(
                DATABASE_URI,
                pool_timeout=5,
                pool_recycle=300,
                pool_pre_ping=True,  # Verify connections before use
                connect_args=connect_args,
                echo=False
            )
        else:
            engine = create_engine(DATABASE_URI)

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
