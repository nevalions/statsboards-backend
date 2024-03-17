from fastapi import Path
from pydantic import BaseModel, ConfigDict
from typing import Annotated, Any

from datetime import datetime as date_type


class MatchDataSchemaBase(BaseModel):
    field_length: int | None = 92
    game_status: Annotated[str, Path(max_length=50)] = "in-progress"
    score_team_a: int | None = 0
    score_team_b: int | None = 0
    timeout_team_a: Annotated[str, Path(max_length=4)] = "●●●"
    timeout_team_b: Annotated[str, Path(max_length=4)] = "●●●"
    qtr: Annotated[str, Path(max_length=10)] = "1st"
    gameclock: Annotated[int, Path(max=10000)] = 720
    gameclock_status: Annotated[str, Path(max_length=50)] = "stopped"
    # playclock: Annotated[int, Path(max=10000)] | None = None
    # playclock_status: Annotated[str, Path(max_length=50)] = "stopped"
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
    gameclock: int | None = None
    gameclock_status: str | None = None
    # playclock: int | None = None
    # playclock_status: str | None = None
    ball_on: int | None = None
    down: str | None = None
    distance: str | None = None

    match_id: int | None = None


class MatchDataSchemaCreate(MatchDataSchemaBase):
    pass


class MatchDataSchema(MatchDataSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
