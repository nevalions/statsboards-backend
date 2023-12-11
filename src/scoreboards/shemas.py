from fastapi import Path
from pydantic import BaseModel, ConfigDict
from typing import Annotated


class ScoreboardSchemaBase(BaseModel):
    is_qtr: bool = True
    is_time: bool = True
    is_playclock: bool = True
    is_downdistance: bool = True
    team_a_color: Annotated[str, Path(max_length=10)] = "#c01c28"
    team_b_color: Annotated[str, Path(max_length=10)] = "#1c71d8"
    match_id: int


class ScoreboardSchemaUpdate(BaseModel):
    is_qtr: bool | None = None
    is_time: bool | None = None
    is_playclock: bool | None = None
    is_downdistance: bool | None = None
    team_a_color: str | None = None
    team_b_color: str | None = None


class ScoreboardSchemaCreate(ScoreboardSchemaBase):
    pass


class ScoreboardSchema(ScoreboardSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
