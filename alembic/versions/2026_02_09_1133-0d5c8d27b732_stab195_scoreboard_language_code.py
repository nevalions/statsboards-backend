"""stab195_scoreboard_language_code

Revision ID: 0d5c8d27b732
Revises: aef5fea559e2
Create Date: 2026-02-09 11:33:05.880906

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0d5c8d27b732"
down_revision: Union[str, None] = "aef5fea559e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "scoreboard",
        sa.Column(
            "language_code",
            sa.String(length=5),
            nullable=True,
            server_default="en",
        ),
    )

    # Ensure existing rows get the expected default.
    op.execute("UPDATE scoreboard SET language_code = 'en' WHERE language_code IS NULL")


def downgrade() -> None:
    op.drop_column("scoreboard", "language_code")
