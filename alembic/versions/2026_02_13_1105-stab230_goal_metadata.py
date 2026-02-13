"""stab230_add_goal_metadata_to_sport_scoreboard_preset

Revision ID: stab230_goal_metadata
Revises: stab228_quick_score_deltas
Create Date: 2026-02-13 11:05:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "stab230_goal_metadata"
down_revision: Union[str, None] = "stab228_quick_score_deltas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column(
            "score_form_goal_label",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'TD'"),
        ),
    )
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column(
            "score_form_goal_emoji",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'🏈'"),
        ),
    )
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column(
            "scoreboard_goal_text",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'TOUCHDOWN'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("sport_scoreboard_preset", "scoreboard_goal_text")
    op.drop_column("sport_scoreboard_preset", "score_form_goal_emoji")
    op.drop_column("sport_scoreboard_preset", "score_form_goal_label")
