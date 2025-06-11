import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.question import Question
from models.quiz import Quiz
from models.user import User

pytestmark = pytest.mark.integration


class TestIntegrationWorkflow:
    """Test the complete workflow from document upload to quiz submission."""

    @patch("main.extract_text_from_pdf")
    @patch("main.generate_quiz_from_text")
    def test_complete_quiz_workflow(
        self,
        mock_generate_quiz,
        mock_extract_text,
        client: TestClient,
        db_session: Session,
        auth_headers: dict,
    ):
        """Test the complete workflow: upload -> generate -> take -> submit quiz."""

        # Step 1: Mock AI services
        mock_extract_text.return_value = "This is test content about geography."
        mock_generate_quiz.return_value = [
            {
                "question": "What is the capital of France?",
                "options": ["Berlin", "Paris", "London", "Madrid"],
                "correct_answer": 1,
            },
            {
                "question": "What is the largest ocean?",
                "options": ["Atlantic", "Pacific", "Indian", "Arctic"],
                "correct_answer": 1,
            },
        ]

        # Step 2: Upload document and generate quiz
        pdf_content = io.BytesIO(b"%PDF-1.5 mock pdf content")
        response = client.post(
            "/api/v1/upload-document",
            headers=auth_headers,
            files={"file": ("geography.pdf", pdf_content, "application/pdf")},
            data={"topic": "Geography", "num_questions": "2"},
        )

        assert response.status_code == 200
        quiz_data = response.json()
        quiz_id = quiz_data["id"]

        # Verify quiz was created in database
        quiz = db_session.query(Quiz).filter(Quiz.id == int(quiz_id)).first()
        assert quiz is not None
        assert quiz.title == "Quiz on Geography"
        assert quiz.topic == "Geography"

        # Verify questions were created
        questions = (
            db_session.query(Question).filter(Question.quiz_id == int(quiz_id)).all()
        )
        assert len(questions) == 2

        # Step 3: Retrieve the quiz
        response = client.get(f"/api/v1/quiz/{quiz_id}")
        assert response.status_code == 200
        retrieved_quiz = response.json()
        assert retrieved_quiz["id"] == quiz_id
        assert len(retrieved_quiz["questions"]) == 2

        # Step 4: Submit answers
        response = client.post(
            "/api/v1/submit-answer",
            json={"quiz_id": int(quiz_id), "answers": [1, 1]},  # Both correct answers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["score"] == 2
        assert result["total"] == 2
        assert result["quiz_id"] == int(quiz_id)

    def test_quiz_with_authentication_flow(
        self, client: TestClient, db_session: Session, test_user: User
    ):
        """Test quiz creation and access with proper authentication."""

        # Step 1: Login
        response = client.post(
            "/api/v1/auth/token",
            data={"username": test_user.email, "password": "testpassword"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Create quiz with authentication
        with patch("main.generate_quiz_from_text") as mock_generate:
            mock_generate.return_value = [
                {
                    "question": "Sample question?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 0,
                }
            ]

            response = client.post(
                "/api/v1/generate-quiz",
                headers=auth_headers,
                json={
                    "content": "Sample content",
                    "topic": "Test Topic",
                    "num_questions": 1,
                },
            )

        assert response.status_code == 200
        quiz_data = response.json()

        # Verify quiz is associated with the user
        quiz = db_session.query(Quiz).filter(Quiz.id == int(quiz_data["id"])).first()
        assert quiz.user_id == test_user.id

    def test_quiz_without_authentication(self, client: TestClient, db_session: Session):
        """Test quiz creation without authentication (anonymous users)."""

        with patch("main.generate_quiz_from_text") as mock_generate:
            mock_generate.return_value = [
                {
                    "question": "Anonymous question?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 0,
                }
            ]

            response = client.post(
                "/api/v1/generate-quiz",
                json={
                    "content": "Anonymous content",
                    "topic": "Anonymous Topic",
                    "num_questions": 1,
                },
            )

        assert response.status_code == 200
        quiz_data = response.json()

        # Verify quiz is not associated with any user
        quiz = db_session.query(Quiz).filter(Quiz.id == int(quiz_data["id"])).first()
        assert quiz.user_id is None

    def test_database_persistence(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """Test that data persists correctly in the database."""

        # Create multiple quizzes
        quiz_ids = []
        for i in range(3):
            with patch("main.generate_quiz_from_text") as mock_generate:
                mock_generate.return_value = [
                    {
                        "question": f"Question {i}?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": i % 4,
                    }
                ]

                response = client.post(
                    "/api/v1/generate-quiz",
                    headers=auth_headers,
                    json={
                        "content": f"Content {i}",
                        "topic": f"Topic {i}",
                        "num_questions": 1,
                    },
                )
                assert response.status_code == 200
                quiz_ids.append(response.json()["id"])

        # Verify all quizzes exist in database
        for quiz_id in quiz_ids:
            quiz = db_session.query(Quiz).filter(Quiz.id == int(quiz_id)).first()
            assert quiz is not None

            questions = (
                db_session.query(Question)
                .filter(Question.quiz_id == int(quiz_id))
                .all()
            )
            assert len(questions) == 1

        # Verify total counts
        total_quizzes = db_session.query(Quiz).count()
        total_questions = db_session.query(Question).count()
        assert total_quizzes == 3
        assert total_questions == 3
