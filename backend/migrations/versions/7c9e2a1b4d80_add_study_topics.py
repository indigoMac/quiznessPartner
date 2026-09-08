"""Add study topics so quizzes from the same material stay grouped.

Revision ID: 7c9e2a1b4d80
Revises: 4b20716d5b5f
Create Date: 2026-09-08 19:20:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "7c9e2a1b4d80"
down_revision: Union[str, None] = "4b20716d5b5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "study_topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("topic", sa.String(), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_study_topics_id"), "study_topics", ["id"], unique=False)

    op.add_column(
        "quizzes", sa.Column("study_topic_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_quizzes_study_topic_id",
        "quizzes",
        "study_topics",
        ["study_topic_id"],
        ["id"],
    )

    conn = op.get_bind()
    quizzes = conn.execute(
        sa.text(
            "SELECT id, user_id, title, topic FROM quizzes WHERE user_id IS NOT NULL"
        )
    ).fetchall()
    for quiz in quizzes:
        title = quiz.topic or quiz.title
        result = conn.execute(
            sa.text(
                "INSERT INTO study_topics (user_id, title, topic) "
                "VALUES (:user_id, :title, :topic) RETURNING id"
            ),
            {"user_id": quiz.user_id, "title": title, "topic": quiz.topic},
        )
        topic_id = result.scalar()
        conn.execute(
            sa.text(
                "UPDATE quizzes SET study_topic_id = :topic_id WHERE id = :quiz_id"
            ),
            {"topic_id": topic_id, "quiz_id": quiz.id},
        )


def downgrade() -> None:
    op.drop_constraint("fk_quizzes_study_topic_id", "quizzes", type_="foreignkey")
    op.drop_column("quizzes", "study_topic_id")
    op.drop_index(op.f("ix_study_topics_id"), table_name="study_topics")
    op.drop_table("study_topics")
