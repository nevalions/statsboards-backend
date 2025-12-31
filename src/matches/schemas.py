from datetime import datetime as date_type

from pydantic import BaseModel, ConfigDict, Field

from src.matchdata.schemas import MatchDataSchemaCreate
from src.scoreboards.schemas import ScoreboardSchemaCreate


class MatchSchemaBase(BaseModel):
    match_date: date_type | None = Field(None, examples=["2024-01-15T15:00:00"])
    week: int = Field(1, examples=[1, 2, 3])
    match_eesl_id: int | None = Field(None, examples=[12345])
    team_a_id: int = Field(..., examples=[1])
    team_b_id: int = Field(..., examples=[2])
    tournament_id: int | None = Field(None, examples=[1])
    sponsor_line_id: int | None = Field(None, examples=[1])
    main_sponsor_id: int | None = Field(None, examples=[5])


class MatchSchemaUpdate(BaseModel):
    match_date: date_type | None = Field(None, examples=["2024-01-15T15:00:00"])
    week: int | None = Field(None, examples=[1, 2, 3])
    match_eesl_id: int | None = Field(None, examples=[12345])
    team_a_id: int | None = Field(None, examples=[1])
    team_b_id: int | None = Field(None, examples=[2])
    tournament_id: int | None = Field(None, examples=[1])
    sponsor_line_id: int | None = Field(None, examples=[1])
    main_sponsor_id: int | None = Field(None, examples=[5])


class MatchSchemaCreate(MatchSchemaBase):
    model_config = ConfigDict(from_attributes=True)


class MatchSchema(MatchSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., examples=[1])


class MatchDataScoreboardSchemaCreate(BaseModel):
    match: MatchSchemaCreate
    match_data: MatchDataSchemaCreate
    scoreboard: ScoreboardSchemaCreate
