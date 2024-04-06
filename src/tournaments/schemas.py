from fastapi import Path
from pydantic import BaseModel, ConfigDict
from typing import Annotated


class TournamentSchemaBase(BaseModel):
    tournament_eesl_id: int | None = None
    title: Annotated[str, Path(max_length=255)] = 'Tournament'
    description: str | None = ''
    tournament_logo_url: str | None = ''
    season_id: int
    sport_id: int
    sponsor_line_id: int | None = None
    main_sponsor_id: int | None = None


class TournamentSchemaUpdate(BaseModel):
    tournament_eesl_id: int | None = None
    title: str | None = None
    description: str | None = None
    tournament_logo_url: str | None = None
    season_id: int | None = None
    sport_id: int | None = None
    sponsor_line_id: int | None = None
    main_sponsor_id: int | None = None


class TournamentSchemaCreate(TournamentSchemaBase):
    pass


class TournamentSchema(TournamentSchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
