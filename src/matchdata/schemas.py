from pydantic import BaseModel, ConfigDict
from typing import Annotated

from datetime import datetime as date_type
from pydantic import BaseModel


class MatchDataSchemaBase(BaseModel):
    score_team_a: int | None = 0
    score_team_b: int | None = 0
    match_id: int


class MatchDataSchemaUpdate(BaseModel):
    score_team_a: int | None = None
    score_team_b: int | None = None


class MatchDataSchemaCreate(MatchDataSchemaBase):
    pass


class MatchDataSchema(MatchDataSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
