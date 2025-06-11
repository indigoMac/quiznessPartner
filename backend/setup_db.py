from auth.auth_utils import get_password_hash
from db import SessionLocal, engine
from models.base import Base
from models.question import Question  # noqa: F401
from models.quiz import Quiz  # noqa: F401
from models.result import Result  # noqa: F401
from models.user import User


def setup_database():
    """Set up the database with tables and a test user."""
    print("Creating database tables...")
    # Make sure all models are imported before creating tables
    Base.metadata.create_all(bind=engine)

    # Create a test user
    db = SessionLocal()
    try:
        # Check if test user already exists
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if not existing_user:
            test_user = User(
                email="test@example.com",
                hashed_password=get_password_hash("testpassword"),
            )
            db.add(test_user)
            db.commit()
            print("Test user created successfully!")
            print("Email: test@example.com")
            print("Password: testpassword")
        else:
            print("Test user already exists!")
    finally:
        db.close()


if __name__ == "__main__":
    setup_database()
