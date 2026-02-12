"""stab207_add_period_config_fields_to_sport_scoreboard_preset

Revision ID: 1b9e2f07a4d1
Revises: 3a874ef6c2db
Create Date: 2026-02-12 19:22:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1b9e2f07a4d1"
down_revision: Union[str, None] = "3a874ef6c2db"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column("has_timeouts", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column("has_playclock", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column("period_mode", sa.String(length=10), nullable=False, server_default="qtr"),
    )
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column("period_labels_json", sa.JSON(), nullable=True),
    )
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column("default_playclock_seconds", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sport_scoreboard_preset", "default_playclock_seconds")
    op.drop_column("sport_scoreboard_preset", "period_labels_json")
    op.drop_column("sport_scoreboard_preset", "period_mode")
    op.drop_column("sport_scoreboard_preset", "has_playclock")
    op.drop_column("sport_scoreboard_preset", "has_timeouts")
