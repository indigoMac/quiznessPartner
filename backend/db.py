import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Get environment (default to development)
ENV = os.getenv("FASTAPI_ENV", "development")

# Database URIs for different environments
DATABASE_URLS = {
    # Use Docker PostgreSQL for development
    "development": "postgresql://postgres:postgres@localhost:5433/quizness",
    # Use Docker PostgreSQL for tests
    "test": "postgresql://postgres:postgres@localhost:5433/quizness_test",
    "production": os.getenv("DATABASE_URL"),  # For production (e.g., Heroku)
}

# Get the appropriate database URL
DATABASE_URI = os.getenv("DATABASE_URI", DATABASE_URLS[ENV])

# For Heroku PostgreSQL which uses DATABASE_URL
if os.getenv("DATABASE_URL"):
    DATABASE_URI = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://")

print(f"Connecting to database: {DATABASE_URI}")
engine = create_engine(DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
