from pydantic import ConfigDict

from datetime import datetime as date_type
from pydantic import BaseModel

from src.matchdata.schemas import MatchDataSchemaCreate
from src.scoreboards.schemas import ScoreboardSchemaCreate


class MatchSchemaBase(BaseModel):
    match_date: date_type | None = None
    week: int = 1
    match_eesl_id: int | None = None
    team_a_id: int
    team_b_id: int
    tournament_id: int | None = None
    sponsor_line_id: int | None = None
    main_sponsor_id: int | None = None


class MatchSchemaUpdate(BaseModel):
    match_date: date_type | None = None
    week: int | None = None
    match_eesl_id: int | None = None
    team_a_id: int | None = None
    team_b_id: int | None = None
    tournament_id: int | None = None
    sponsor_line_id: int | None = None
    main_sponsor_id: int | None = None


class MatchSchemaCreate(MatchSchemaBase):
    model_config = ConfigDict(from_attributes=True)


class MatchSchema(MatchSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MatchDataScoreboardSchemaCreate(BaseModel):
    match: MatchSchemaCreate
    match_data: MatchDataSchemaCreate
    scoreboard: ScoreboardSchemaCreate
