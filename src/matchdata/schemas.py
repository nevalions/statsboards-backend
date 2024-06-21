from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict


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


class MatchDataSchemaUpdate(BaseModel):
    field_length: int | None = None
    game_status: str | None = None
    score_team_a: int | None = None
    score_team_b: int | None = None
    timeout_team_a: str | None = None
    timeout_team_b: str | None = None
    qtr: str | None = None
    ball_on: int | None = None
    down: str | None = None
    distance: str | None = None

    match_id: int | None = None


class MatchDataSchemaCreate(MatchDataSchemaBase):
    pass


class MatchDataSchema(MatchDataSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
