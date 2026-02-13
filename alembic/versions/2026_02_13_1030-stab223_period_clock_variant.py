"""stab223_add_period_clock_variant_to_sport_scoreboard_preset

Revision ID: stab223_period_clock_variant
Revises: stab211_period_canonical
Create Date: 2026-02-13 10:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "stab223_period_clock_variant"
down_revision: Union[str, None] = "stab211_period_canonical"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column(
            "period_clock_variant",
            sa.String(length=10),
            nullable=False,
            server_default="per_period",
        ),
    )


def downgrade() -> None:
    op.drop_column("sport_scoreboard_preset", "period_clock_variant")
