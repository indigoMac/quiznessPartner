"""Add one episode script per study topic.

Revision ID: c3a91e7b5f28
Revises: a4c8e2f91b07
Create Date: 2026-10-06 19:50:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3a91e7b5f28"
down_revision: Union[str, None] = "a4c8e2f91b07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("study_topic_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("script", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["study_topic_id"], ["study_topics.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("study_topic_id", name="uq_episodes_study_topic_id"),
    )
    op.create_index(op.f("ix_episodes_id"), "episodes", ["id"], unique=False)
    op.create_index(op.f("ix_episodes_user_id"), "episodes", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_episodes_user_id"), table_name="episodes")
    op.drop_index(op.f("ix_episodes_id"), table_name="episodes")
    op.drop_table("episodes")
