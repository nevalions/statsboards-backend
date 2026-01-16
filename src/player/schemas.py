from typing import TYPE_CHECKING, Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict, Field

from src.core.schema_helpers import PaginationMetadata, make_fields_optional

if TYPE_CHECKING:
    from src.person.schemas import PersonSchema
    from src.player_team_tournament.schemas import PlayerTeamTournamentWithFullDetailsSchema
    from src.sports.schemas import SportSchema


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
    person: "PersonSchema | None" = Field(None, description="Person with full details")
    sport: "SportSchema | None" = Field(None, description="Sport with full details")
    player_team_tournaments: list["PlayerTeamTournamentWithFullDetailsSchema"] = Field(
        default_factory=list, description="Player team tournament associations with nested details"
    )


class PaginatedPlayerWithFullDetailsResponse(BaseModel):
    data: list["PlayerWithFullDetailsSchema"]
    metadata: PaginationMetadata


class PaginatedPlayerWithDetailsResponse(BaseModel):
    data: list["PlayerWithDetailsSchema"]
    metadata: PaginationMetadata
