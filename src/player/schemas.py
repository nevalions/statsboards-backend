from typing import Annotated, Any

from fastapi import Path
from pydantic import BaseModel, ConfigDict, Field

from src.core.schema_helpers import PaginationMetadata, make_fields_optional


class PlayerSchemaBase(BaseModel):
    sport_id: int | None = Field(None, examples=[1])
    person_id: int | None = Field(None, examples=[1])
    player_eesl_id: int | None = Field(None, examples=[98765])
    isprivate: bool = Field(False, examples=[False, True])
    user_id: int | None = Field(None, examples=[1])


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


class PlayerTeamTournamentInfoSchema(BaseModel):
    id: int
    player_team_tournament_eesl_id: int | None = None
    player_number: Annotated[str, Path(max_length=10)] | None = "0"
    team_id: int | None = None
    team_title: str | None = None
    position_id: int | None = None
    position_title: str | None = None
    tournament_id: int | None = None


class PlayerWithDetailsSchema(PlayerSchema):
    first_name: str | None = Field(None, description="Person's first name")
    second_name: str | None = Field(None, description="Person's second name")
    player_team_tournaments: list[PlayerTeamTournamentInfoSchema] = Field(
        default_factory=list, description="Player team tournament associations"
    )


class PlayerWithFullDetailsSchema(PlayerSchema):
    person: Any = Field(None, description="Person with full details")
    sport: Any = Field(None, description="Sport with full details")
    player_team_tournaments: list[Any] = Field(
        default_factory=list, description="Player team tournament associations with nested details"
    )


class PaginatedPlayerWithFullDetailsResponse(BaseModel):
    data: list["PlayerWithFullDetailsSchema"]
    metadata: PaginationMetadata


class PaginatedPlayerWithDetailsResponse(BaseModel):
    data: list["PlayerWithDetailsSchema"]
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


PlayerWithFullDetailsSchema.model_rebuild()
PaginatedPlayerWithFullDetailsResponse.model_rebuild()
PaginatedPlayerWithDetailsResponse.model_rebuild()
