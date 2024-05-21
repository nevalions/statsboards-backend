from fastapi import Path
from pydantic import BaseModel, ConfigDict
from typing import Annotated


class PlayerMatchSchemaBase(BaseModel):
    player_match_eesl_id: int | None = None
    player_team_tournament_id: int | None = None
    match_position_id: int | None = None
    match_id: int
    match_number: Annotated[str, Path(max_length=10)] | None = '0'
    team_id: int
    is_start: bool | None = False


class PlayerMatchSchemaUpdate(BaseModel):
    player_match_eesl_id: int | None = None
    player_team_tournament_id: int | None = None
    match_position_id: int | None = None
    match_id: int | None = None
    match_number: str | None = None
    team_id: int | None = None
    is_start: bool | None = None


class PlayerMatchSchemaCreate(PlayerMatchSchemaBase):
    pass


class PlayerMatchSchema(PlayerMatchSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
