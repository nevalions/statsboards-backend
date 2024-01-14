from fastapi import Path
from pydantic import BaseModel, ConfigDict
from typing import Annotated


class TournamentSchemaBase(BaseModel):
    tournament_eesl_id: int | None = None
    title: Annotated[str, Path(max_length=255)]
    description: str | None = None
    tournament_logo_url: str | None = None
    season_id: int
    sport_id: int


class TournamentSchemaUpdate(BaseModel):
    tournament_eesl_id: int | None = None
    title: str | None = None
    description: str | None = None
    tournament_logo_url: str | None = None
    season_id: int | None = None
    sport_id: int


class TournamentSchemaCreate(TournamentSchemaBase):
    pass


class TournamentSchema(TournamentSchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
