"""stab228_add_quick_score_deltas_to_sport_scoreboard_preset

Revision ID: stab228_quick_score_deltas
Revises: stab223_period_clock_variant
Create Date: 2026-02-13 10:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "stab228_quick_score_deltas"
down_revision: Union[str, None] = "stab223_period_clock_variant"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column(
            "quick_score_deltas",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[6, 3, 2, 1, -1]'::json"),
        ),
    )


def downgrade() -> None:
    op.drop_column("sport_scoreboard_preset", "quick_score_deltas")
