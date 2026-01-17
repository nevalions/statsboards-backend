from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.core.schema_helpers import PaginationMetadata, make_fields_optional
from src.core.shared_schemas import (
    PlayerTeamTournamentBaseFields,
    PlayerTeamTournamentWithTitles,
)
from src.positions.schemas import PositionSchema
from src.teams.schemas import TeamSchema
from src.tournaments.schemas import TournamentSchema


class PlayerTeamTournamentSchemaBase(PlayerTeamTournamentBaseFields):
    pass


PlayerTeamTournamentSchemaUpdate = make_fields_optional(PlayerTeamTournamentSchemaBase)


class PlayerTeamTournamentSchemaCreate(PlayerTeamTournamentSchemaBase):
    pass


class PlayerTeamTournamentSchema(PlayerTeamTournamentSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class PlayerTeamTournamentWithDetailsSchema(PlayerTeamTournamentWithTitles):
    player_id: int
    first_name: str | None = None
    second_name: str | None = None


class PlayerTeamTournamentWithDetailsAndPhotosSchema(PlayerTeamTournamentWithTitles):
    """Mixed schema with player details and person photo fields for tournament players display."""

    player_id: int
    first_name: str | None = None
    second_name: str | None = None
    person_photo_url: str | None = ""
    person_photo_icon_url: str | None = ""


class PlayerTeamTournamentWithFullDetailsSchema(PlayerTeamTournamentBaseFields):
    id: int
    team: TeamSchema | None = Field(None, description="Team with full details")
    tournament: TournamentSchema | None = Field(None, description="Tournament with full details")
    position: PositionSchema | None = Field(None, description="Position with full details")
    model_config = ConfigDict(from_attributes=True)


class PlayerTeamTournamentWithFullDetailsSchemaRef(PlayerTeamTournamentBaseFields):
    """Reference schema for use in PlayerWithFullDetailsSchema"""

    id: int
    team: TeamSchema | None = Field(None, description="Team with full details")
    tournament: TournamentSchema | None = Field(None, description="Tournament with full details")
    position: PositionSchema | None = Field(None, description="Position with full details")
    model_config = ConfigDict(from_attributes=True)


class PaginatedPlayerTeamTournamentResponse(BaseModel):
    data: list[PlayerTeamTournamentSchema]
    metadata: PaginationMetadata


class PaginatedPlayerTeamTournamentWithDetailsResponse(BaseModel):
    data: list[PlayerTeamTournamentWithDetailsSchema]
    metadata: PaginationMetadata


class PaginatedPlayerTeamTournamentWithFullDetailsResponse(BaseModel):
    data: list[PlayerTeamTournamentWithFullDetailsSchema]
    metadata: PaginationMetadata


class PaginatedPlayerTeamTournamentWithDetailsAndPhotosResponse(BaseModel):
    data: list[PlayerTeamTournamentWithDetailsAndPhotosSchema]
    metadata: PaginationMetadata
