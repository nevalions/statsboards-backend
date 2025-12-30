"""add missing performance indexes

Revision ID: a3b4c5d6e7f8
Revises: 2cf1902c7d5c
Create Date: 2025-12-30 16:25:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, None] = "2cf1902c7d5c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # player_match: (match_id, player_match_eesl_id)
    op.create_index(
        "ix_player_match_match_id_player_match_eesl_id",
        "player_match",
        ["match_id", "player_match_eesl_id"]
    )
    
    # football_event: (match_id)
    op.create_index(
        "ix_football_event_match_id",
        "football_event",
        ["match_id"]
    )
    
    # scoreboard: (match_id, player_match_lower_id)
    op.create_index(
        "ix_scoreboard_match_id_player_match_lower_id",
        "scoreboard",
        ["match_id", "player_match_lower_id"]
    )
    
    # player_team_tournament: (tournament_id, player_id)
    op.create_index(
        "ix_player_team_tournament_tournament_id_player_id",
        "player_team_tournament",
        ["tournament_id", "player_id"]
    )
    
    # match: (tournament_id, team_a_id, team_b_id)
    op.create_index(
        "ix_match_tournament_id_team_a_id_team_b_id",
        "match",
        ["tournament_id", "team_a_id", "team_b_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_match_tournament_id_team_a_id_team_b_id", table_name="match")
    op.drop_index("ix_player_team_tournament_tournament_id_player_id", table_name="player_team_tournament")
    op.drop_index("ix_scoreboard_match_id_player_match_lower_id", table_name="scoreboard")
    op.drop_index("ix_football_event_match_id", table_name="football_event")
    op.drop_index("ix_player_match_match_id_player_match_eesl_id", table_name="player_match")
