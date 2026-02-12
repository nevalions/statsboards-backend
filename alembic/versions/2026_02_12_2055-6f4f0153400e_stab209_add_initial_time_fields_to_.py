"""stab209_add_initial_time_fields_to_sport_scoreboard_preset

Revision ID: 6f4f0153400e
Revises: 1b9e2f07a4d1
Create Date: 2026-02-12 20:55:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6f4f0153400e"
down_revision: Union[str, None] = "1b9e2f07a4d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column(
            "initial_time_mode",
            sa.String(length=10),
            nullable=False,
            server_default="max",
        ),
    )
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column("initial_time_min_seconds", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sport_scoreboard_preset", "initial_time_min_seconds")
    op.drop_column("sport_scoreboard_preset", "initial_time_mode")
