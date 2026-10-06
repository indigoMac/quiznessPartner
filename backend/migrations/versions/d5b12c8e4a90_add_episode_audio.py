"""Add audio status and timings to episodes.

Revision ID: d5b12c8e4a90
Revises: c3a91e7b5f28
Create Date: 2026-10-06 22:10:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d5b12c8e4a90"
down_revision: Union[str, None] = "c3a91e7b5f28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "episodes",
        sa.Column(
            "audio_status",
            sa.String(),
            nullable=False,
            server_default="none",
        ),
    )
    op.add_column("episodes", sa.Column("audio_error", sa.Text(), nullable=True))
    op.add_column(
        "episodes", sa.Column("duration_seconds", sa.Float(), nullable=True)
    )
    op.add_column("episodes", sa.Column("segment_timings", sa.JSON(), nullable=True))
    op.add_column("episodes", sa.Column("audio_key", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("episodes", "audio_key")
    op.drop_column("episodes", "segment_timings")
    op.drop_column("episodes", "duration_seconds")
    op.drop_column("episodes", "audio_error")
    op.drop_column("episodes", "audio_status")
