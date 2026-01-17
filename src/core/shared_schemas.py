from typing import Annotated

from fastapi import Path
from pydantic import BaseModel


class PlayerTeamTournamentBaseFields(BaseModel):
    """Base fields shared across player team tournament related schemas"""

    player_team_tournament_eesl_id: int | None = None
    player_id: int
    player_number: Annotated[str, Path(max_length=10)] | None = "0"
    team_id: int | None = None
    tournament_id: int | None = None
    position_id: int | None = None


class PlayerTeamTournamentWithTitles(BaseModel):
    """Base fields including related title fields"""

    id: int
    player_team_tournament_eesl_id: int | None = None
    player_number: Annotated[str, Path(max_length=10)] | None = "0"
    team_id: int | None = None
    team_title: str | None = None
    position_id: int | None = None
    position_title: str | None = None
    tournament_id: int | None = None
