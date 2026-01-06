from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import make_fields_optional


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


class PaginationMetadata(BaseModel):
    page: int
    items_per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedPlayerTeamTournamentResponse(BaseModel):
    data: list[PlayerTeamTournamentSchema]
    metadata: PaginationMetadata
