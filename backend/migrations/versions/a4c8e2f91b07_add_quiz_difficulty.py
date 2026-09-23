"""Store the requested difficulty on each quiz.

Revision ID: a4c8e2f91b07
Revises: 9d1f3c7a2e64
Create Date: 2026-09-23 12:40:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a4c8e2f91b07"
down_revision: Union[str, None] = "9d1f3c7a2e64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "quizzes",
        sa.Column(
            "difficulty",
            sa.String(),
            nullable=False,
            server_default="medium",
        ),
    )


def downgrade() -> None:
    op.drop_column("quizzes", "difficulty")
