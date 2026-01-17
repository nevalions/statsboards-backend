from __future__ import annotations

from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import make_fields_optional


class MatchDataSchemaBase(BaseModel):
    field_length: int | None = 92
    game_status: Annotated[str, Path(max_length=50)] = "in-progress"
    score_team_a: int | None = 0
    score_team_b: int | None = 0
    timeout_team_a: Annotated[str, Path(max_length=4)] = "●●●"
    timeout_team_b: Annotated[str, Path(max_length=4)] = "●●●"
    qtr: Annotated[str, Path(max_length=10)] = "1st"
    ball_on: Annotated[int, Path(max=200)] = 20
    down: Annotated[str, Path(max_length=10)] = "1st"
    distance: Annotated[str, Path(max_length=20)] = "10"

    match_id: int | None = None


MatchDataSchemaUpdate = make_fields_optional(MatchDataSchemaBase)


class MatchDataSchemaCreate(MatchDataSchemaBase):
    pass


class MatchDataSchema(MatchDataSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
