"""stab211_add_canonical_period_fields_for_preset_scoreboard_matchdata

Revision ID: stab211_period_canonical
Revises: 6f4f0153400e
Create Date: 2026-02-13 09:15:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "stab211_period_canonical"
down_revision: Union[str, None] = "6f4f0153400e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sport_scoreboard_preset",
        sa.Column("period_count", sa.Integer(), nullable=False, server_default="4"),
    )
    op.execute(
        """
        UPDATE sport_scoreboard_preset
        SET period_count = json_array_length(period_labels_json)
        WHERE period_mode = 'custom'
          AND period_labels_json IS NOT NULL;
        """
    )

    op.add_column(
        "scoreboard",
        sa.Column("period_mode", sa.String(length=10), nullable=False, server_default="qtr"),
    )
    op.add_column(
        "scoreboard",
        sa.Column("period_count", sa.Integer(), nullable=False, server_default="4"),
    )
    op.add_column(
        "scoreboard",
        sa.Column("period_labels_json", sa.JSON(), nullable=True),
    )

    op.execute(
        """
        UPDATE scoreboard AS sb
        SET
            period_mode = preset.period_mode,
            period_count = preset.period_count,
            period_labels_json = preset.period_labels_json
        FROM match AS m
        JOIN tournament AS t ON t.id = m.tournament_id
        JOIN sport AS s ON s.id = t.sport_id
        JOIN sport_scoreboard_preset AS preset ON preset.id = s.scoreboard_preset_id
        WHERE sb.match_id = m.id
          AND sb.use_sport_preset = TRUE;
        """
    )

    op.add_column(
        "matchdata",
        sa.Column("period_key", sa.String(length=50), nullable=False, server_default="period.1"),
    )
    op.execute(
        """
        UPDATE matchdata
        SET period_key = CASE lower(trim(coalesce(qtr, '')))
            WHEN '1st' THEN 'period.1'
            WHEN '2nd' THEN 'period.2'
            WHEN '3rd' THEN 'period.3'
            WHEN '4th' THEN 'period.4'
            ELSE 'period.1'
        END;
        """
    )


def downgrade() -> None:
    op.drop_column("matchdata", "period_key")
    op.drop_column("scoreboard", "period_labels_json")
    op.drop_column("scoreboard", "period_count")
    op.drop_column("scoreboard", "period_mode")
    op.drop_column("sport_scoreboard_preset", "period_count")
