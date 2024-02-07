from fastapi import Path
from pydantic import BaseModel, ConfigDict
from typing import Annotated


class TeamSchemaBase(BaseModel):
    team_eesl_id: int | None = None
    title: Annotated[str, Path(max_length=50)]
    city: Annotated[str, Path(max_length=50)] | None = None
    description: str | None = None
    team_logo_url: str | None = None
    sport_id: int


class TeamSchemaUpdate(BaseModel):
    title: str | None = None
    city: str | None = None
    description: str | None = None
    team_logo_url: str | None = None
    sport_id: int | None = None


class TeamSchemaCreate(TeamSchemaBase):
    pass


class TeamSchema(TeamSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
