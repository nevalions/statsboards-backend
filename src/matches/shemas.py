from fastapi import Path
from pydantic import BaseModel, ConfigDict
from typing import Annotated

from datetime import datetime as date_type
from pydantic import BaseModel

from src.matchdata.schemas import MatchDataSchemaCreate
from src.scoreboards.shemas import ScoreboardSchemaCreate


class MatchSchemaBase(BaseModel):
    match_eesl_id: int | None = None
    team_a_id: int
    team_b_id: int
    tournament_id: int | None = None


class MatchSchemaUpdate(BaseModel):
    match_eesl_id: int | None = None
    team_a_id: int | None = None
    team_b_id: int | None = None
    tournament_id: int | None = None


class MatchSchemaCreate(MatchSchemaBase):
    pass


class MatchSchema(MatchSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MatchDataScoreboardSchemaCreate(BaseModel):
    match: MatchSchemaCreate
    match_data: MatchDataSchemaCreate
    scoreboard: ScoreboardSchemaCreate
