from __future__ import annotations

from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import make_fields_optional


class PlayerMatchSchemaBase(BaseModel):
    player_match_eesl_id: int | None = None
    player_team_tournament_id: int | None = None
    match_position_id: int | None = None
    match_id: int
    match_number: Annotated[str, Path(max_length=10)] | None = "0"
    team_id: int
    is_start: bool | None = False
    is_starting: bool | None = False
    starting_type: str | None = None


PlayerMatchSchemaUpdate = make_fields_optional(PlayerMatchSchemaBase)


class PlayerMatchSchemaCreate(PlayerMatchSchemaBase):
    pass


class PlayerMatchSchema(PlayerMatchSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
