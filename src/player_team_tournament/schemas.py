from typing import TYPE_CHECKING, Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict, Field

from src.core.schema_helpers import PaginationMetadata, make_fields_optional

if TYPE_CHECKING:
    from src.positions.schemas import PositionSchema
    from src.teams.schemas import TeamSchema
    from src.tournaments.schemas import TournamentSchema


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


class PlayerTeamTournamentWithFullDetailsSchema(BaseModel):
    id: int
    player_team_tournament_eesl_id: int | None = None
    player_id: int
    player_number: Annotated[str, Path(max_length=10)] | None = "0"
    team: "TeamSchema | None" = Field(None, description="Team with full details")
    tournament: "TournamentSchema | None" = Field(None, description="Tournament with full details")
    position: "PositionSchema | None" = Field(None, description="Position with full details")
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
