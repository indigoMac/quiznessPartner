"""Unit tests for database helper functions."""

from db_utils import create_quiz, list_user_quizzes, record_quiz_result
from models.result import Result
from tests.fixtures.factories import QuestionFactory, QuizFactory, UserFactory


class TestListUserQuizzes:
    def test_empty_list_for_user_without_quizzes(self, db_session):
        user = UserFactory.create(db_session)
        db_session.commit()

        quizzes, total, completed = list_user_quizzes(db_session, user.id)

        assert quizzes == []
        assert total == 0
        assert completed == 0

    def test_returns_only_the_current_users_quizzes(self, db_session):
        owner = UserFactory.create(db_session)
        other = UserFactory.create(db_session)
        owned = QuizFactory.create(db_session, user=owner, title="Mine", topic="Math")
        QuizFactory.create(db_session, user=other, title="Theirs")
        QuestionFactory.create_batch(2, db_session, quiz=owned)
        db_session.commit()

        quizzes, total, completed = list_user_quizzes(db_session, owner.id)

        assert total == 1
        assert completed == 0
        assert quizzes[0]["id"] == owned.id
        assert quizzes[0]["title"] == "Mine"
        assert quizzes[0]["question_count"] == 2
        assert quizzes[0]["attempt_count"] == 0
        assert quizzes[0]["best_score"] is None

    def test_includes_attempt_stats_and_completed_count(self, db_session):
        user = UserFactory.create(db_session)
        quiz = QuizFactory.create(db_session, user=user, title="History")
        QuestionFactory.create_batch(3, db_session, quiz=quiz)
        record_quiz_result(db_session, quiz.id, score=1, total=3, answers=[0, 1, 2], user_id=user.id)
        record_quiz_result(db_session, quiz.id, score=3, total=3, answers=[0, 1, 2], user_id=user.id)
        db_session.commit()

        quizzes, total, completed = list_user_quizzes(db_session, user.id)

        assert total == 1
        assert completed == 1
        assert quizzes[0]["attempt_count"] == 2
        assert quizzes[0]["best_score"] == 3


class TestRecordQuizResult:
    def test_stores_user_id_when_provided(self, db_session):
        user = UserFactory.create(db_session)
        quiz = create_quiz(db_session, title="Test", topic="Topic", user_id=user.id)

        result = record_quiz_result(
            db_session, quiz.id, score=2, total=4, answers=[0, 1], user_id=user.id
        )

        stored = db_session.query(Result).filter(Result.id == result.id).first()
        assert stored.user_id == user.id
        assert stored.score == 2
        assert stored.answers == [0, 1]

    def test_allows_anonymous_results(self, db_session):
        quiz = create_quiz(db_session, title="Public", topic="Topic")

        result = record_quiz_result(
            db_session, quiz.id, score=0, total=1, answers=[3], user_id=None
        )

        stored = db_session.query(Result).filter(Result.id == result.id).first()
        assert stored.user_id is None
