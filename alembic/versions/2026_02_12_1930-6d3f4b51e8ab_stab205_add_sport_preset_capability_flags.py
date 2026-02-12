"""stab205_add_sport_preset_capability_flags

Revision ID: 6d3f4b51e8ab
Revises: 3a874ef6c2db
Create Date: 2026-02-12 19:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6d3f4b51e8ab"
down_revision: Union[str, None] = "3a874ef6c2db"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column("has_playclock", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column("has_timeouts", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column("sport_scoreboard_preset", "has_timeouts")
    op.drop_column("sport_scoreboard_preset", "has_playclock")
