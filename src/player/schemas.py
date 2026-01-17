from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.core.schema_helpers import PaginationMetadata, make_fields_optional
from src.core.shared_schemas import PlayerTeamTournamentWithTitles, PrivacyFieldsBase
from src.person.schemas import PersonSchema
from src.sports.schemas import SportSchema


class PlayerSchemaBase(PrivacyFieldsBase):
    sport_id: int | None = Field(None, examples=[1])
    person_id: int | None = Field(None, examples=[1])
    player_eesl_id: int | None = Field(None, examples=[98765])


PlayerSchemaUpdate = make_fields_optional(PlayerSchemaBase)


class PlayerSchemaCreate(PlayerSchemaBase):
    pass


class PlayerAddToSportSchema(BaseModel):
    person_id: int = Field(..., description="Person ID to add as player")
    sport_id: int = Field(..., description="Sport ID to add player to")
    isprivate: bool | None = Field(None, examples=[False])
    user_id: int | None = Field(None, examples=[1])


class PlayerSchema(PlayerSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., examples=[1])


class PlayerWithDetailsSchema(PlayerSchema):
    first_name: str | None = Field(None, description="Person's first name")
    second_name: str | None = Field(None, description="Person's second name")
    player_team_tournaments: list[PlayerTeamTournamentWithTitles] = Field(
        default_factory=list, description="Player team tournament associations"
    )


class PlayerWithDetailsAndPhotosSchema(PlayerWithDetailsSchema):
    """Mixed schema with player details and person photo fields for sport players display."""

    person_photo_url: str | None = ""
    person_photo_icon_url: str | None = ""


class PaginatedPlayerWithDetailsAndPhotosResponse(BaseModel):
    data: list[PlayerWithDetailsAndPhotosSchema]
    metadata: PaginationMetadata


class PlayerWithFullDetailsSchema(PlayerSchema):
    person: PersonSchema | None = Field(None, description="Person with full details")
    sport: SportSchema | None = Field(None, description="Sport with full details")
    player_team_tournaments: list[PlayerTeamTournamentWithTitles] = Field(
        default_factory=list, description="Player team tournament associations with nested details"
    )


class PaginatedPlayerWithFullDetailsResponse(BaseModel):
    data: list[PlayerWithFullDetailsSchema]
    metadata: PaginationMetadata


class PaginatedPlayerWithDetailsResponse(BaseModel):
    data: list[PlayerWithDetailsSchema]
    metadata: PaginationMetadata


class TeamAssignmentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int | None = None
    team_title: str | None = None
    position_id: int | None = None
    position_title: str | None = None
    player_number: str | None = None
    tournament_id: int | None = None
    tournament_title: str | None = None
    season_id: int | None = None
    season_year: int | None = None


class CareerByTeamSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: int | None = None
    team_title: str | None = None
    assignments: list[TeamAssignmentSchema] = Field(default_factory=list)


class CareerByTournamentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tournament_id: int | None = None
    tournament_title: str | None = None
    season_id: int | None = None
    season_year: int | None = None
    assignments: list[TeamAssignmentSchema] = Field(default_factory=list)


class PlayerCareerResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    career_by_team: list[CareerByTeamSchema] = Field(default_factory=list)
    career_by_tournament: list[CareerByTournamentSchema] = Field(default_factory=list)


class TournamentAssignmentSchema(BaseModel):
    """Specific tournament assignment for a player"""

    model_config = ConfigDict(from_attributes=True)

    team_title: str | None = None
    team_id: int | None = None
    position_title: str | None = None
    position_id: int | None = None
    player_number: str | None = None
    tournament_title: str | None = None
    tournament_year: str | None = None
    tournament_id: int | None = None


class PlayerDetailInTournamentResponse(BaseModel):
    """Player detail in tournament context"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sport_id: int
    person: PersonSchema
    sport: SportSchema
    tournament_assignment: TournamentAssignmentSchema
    career_by_team: list[CareerByTeamSchema] = Field(default_factory=list)
    career_by_tournament: list[CareerByTournamentSchema] = Field(default_factory=list)
