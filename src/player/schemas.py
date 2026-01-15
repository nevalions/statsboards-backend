from typing import Annotated

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


class PlayerWithDetailsSchema(BaseModel):
    id: int
    sport_id: int | None = None
    person_id: int | None = None
    player_eesl_id: int | None = None
    first_name: str | None = None
    second_name: str | None = None
    player_team_tournaments: list[PlayerTeamTournamentInfoSchema] = []


class PaginatedPlayerWithDetailsResponse(BaseModel):
    data: list[PlayerWithDetailsSchema]
    metadata: PaginationMetadata
