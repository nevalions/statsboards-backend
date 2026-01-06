from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import make_fields_optional, PaginationMetadata


class PlayerTeamTournamentSchemaBase(BaseModel):
    player_team_tournament_eesl_id: int | None = None
    player_id: int
    position_id: int | None = None
    team_id: int | None = None
    tournament_id: int | None = None
    player_number: Annotated[str, Path(max_length=10)] | None = "0"


PlayerTeamTournamentSchemaUpdate = make_fields_optional(PlayerTeamTournamentSchemaBase)


class PlayerTeamTournamentSchemaCreate(PlayerTeamTournamentSchemaBase):
    pass


class PlayerTeamTournamentSchema(PlayerTeamTournamentSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class PlayerTeamTournamentWithDetailsSchema(BaseModel):
    id: int
    player_team_tournament_eesl_id: int | None = None
    player_id: int
    position_id: int | None = None
    team_id: int | None = None
    tournament_id: int | None = None
    player_number: Annotated[str, Path(max_length=10)] | None = "0"
    first_name: str | None = None
    second_name: str | None = None
    team_title: str | None = None
    position_title: str | None = None


class PaginatedPlayerTeamTournamentResponse(BaseModel):
    data: list[PlayerTeamTournamentSchema]
    metadata: PaginationMetadata


class PaginatedPlayerTeamTournamentWithDetailsResponse(BaseModel):
    data: list[PlayerTeamTournamentWithDetailsSchema]
    metadata: PaginationMetadata
