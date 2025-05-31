from auth.auth_utils import get_password_hash
from db import SessionLocal
from models.question import Question
from models.quiz import Quiz
from models.user import User


def seed_database():
    """Seed the database with initial data"""
    db = SessionLocal()
    try:
        # Create test user if doesn't exist
        if not db.query(User).filter(User.email == "test@example.com").first():
            test_user = User(
                email="test@example.com",
                hashed_password=get_password_hash("testpassword"),
                is_active=True,
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print("Created test user:")
            print("  Email: test@example.com")
            print("  Password: testpassword")

            # Create a sample quiz
            quiz = Quiz(
                title="Sample Quiz", topic="General Knowledge", user_id=test_user.id
            )
            db.add(quiz)
            db.commit()
            db.refresh(quiz)

            # Add some questions
            questions = [
                Question(
                    quiz_id=quiz.id,
                    question_text="What is the capital of France?",
                    options=["London", "Paris", "Berlin", "Madrid"],
                    correct_answer=1,
                ),
                Question(
                    quiz_id=quiz.id,
                    question_text="Who wrote 'Romeo and Juliet'?",
                    options=[
                        "Charles Dickens",
                        "William Shakespeare",
                        "Jane Austen",
                        "Mark Twain",
                    ],
                    correct_answer=1,
                ),
            ]
            db.bulk_save_objects(questions)
            db.commit()
            print("Created sample quiz with questions")
        else:
            print("Test user already exists")

    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding database...")
    seed_database()
    print("Done!")
