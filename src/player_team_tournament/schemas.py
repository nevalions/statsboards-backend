from fastapi import Path
from pydantic import BaseModel, ConfigDict
from typing import Annotated


class PlayerTeamTournamentSchemaBase(BaseModel):
    player_team_tournament_eesl_id: int | None = None
    player_id: int
    team_id: int | None = None
    tournament_id: int | None = None
    player_number: Annotated[str, Path(max_length=10)] = '0'
    player_position: Annotated[str, Path(max_length=20)] | None = 'POS'


class PlayerTeamTournamentSchemaUpdate(BaseModel):
    player_team_tournament_eesl_id: int | None = None
    player_id: int | None = None
    team_id: int | None = None
    tournament_id: int | None = None
    player_number: str | None = None
    player_position: str | None = None


class PlayerTeamTournamentSchemaCreate(PlayerTeamTournamentSchemaBase):
    pass


class PlayerTeamTournamentSchema(PlayerTeamTournamentSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
