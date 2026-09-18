"""Add embedded source chunks so quiz content can be grounded in passages.

Requires the pgvector extension, which ships with the pgvector/pgvector
images used by docker-compose and CI.

Revision ID: 9d1f3c7a2e64
Revises: 7c9e2a1b4d80
Create Date: 2026-09-12 16:40:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "9d1f3c7a2e64"
down_revision: Union[str, None] = "7c9e2a1b4d80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSIONS = 1536


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "source_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("study_topic_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["study_topic_id"], ["study_topics.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_source_chunks_id"), "source_chunks", ["id"], unique=False)
    op.create_index(
        op.f("ix_source_chunks_study_topic_id"),
        "source_chunks",
        ["study_topic_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_source_chunks_topic_index",
        "source_chunks",
        ["study_topic_id", "chunk_index"],
    )

    # HNSW gives better recall than IVFFlat and, unlike IVFFlat, does not need
    # to be built against existing rows, so it works on an empty table.
    op.execute(
        "CREATE INDEX ix_source_chunks_embedding ON source_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_source_chunks_embedding")
    op.drop_constraint(
        "uq_source_chunks_topic_index", "source_chunks", type_="unique"
    )
    op.drop_index(op.f("ix_source_chunks_study_topic_id"), table_name="source_chunks")
    op.drop_index(op.f("ix_source_chunks_id"), table_name="source_chunks")
    op.drop_table("source_chunks")
