from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict, Field

from src.core.schema_helpers import PaginationMetadata, make_fields_optional
from src.seasons.schemas import SeasonSchema
from src.sponsor_lines.schemas import SponsorLineSchema
from src.sponsors.schemas import SponsorSchema
from src.sports.schemas import SportSchema
from src.teams.schemas import TeamSchema


class TournamentSchemaBase(BaseModel):
    tournament_eesl_id: int | None = Field(None, examples=[67890])
    title: Annotated[str, Path(max_length=255)] = Field(
        "Tournament", examples=["Premier League", "La Liga"]
    )
    description: str | None = Field("", examples=["Top tier English football league"])
    tournament_logo_url: Annotated[str, Path(max_length=500)] | None = Field(
        "", examples=["https://example.com/logos/premier-league.png"]
    )
    tournament_logo_icon_url: Annotated[str, Path(max_length=500)] | None = Field(
        "", examples=["https://example.com/icons/premier-league-icon.png"]
    )
    tournament_logo_web_url: Annotated[str, Path(max_length=500)] | None = Field(
        "", examples=["https://example.com/web/premier-league.png"]
    )
    season_id: int = Field(..., examples=[1])
    sport_id: int = Field(..., examples=[1])
    sponsor_line_id: int | None = Field(None, examples=[1])
    main_sponsor_id: int | None = Field(None, examples=[5])
    isprivate: bool = Field(False, examples=[False, True])
    user_id: int | None = Field(None, examples=[1])


TournamentSchemaUpdate = make_fields_optional(TournamentSchemaBase)


class TournamentSchemaCreate(TournamentSchemaBase):
    pass


class UploadTournamentLogoResponse(BaseModel):
    logoUrl: str = Field(..., examples=["https://example.com/uploads/logos/premier-league.png"])


class UploadResizeTournamentLogoResponse(BaseModel):
    original: str = Field(..., examples=["https://example.com/uploads/logos/premier-league.png"])
    icon: str = Field(..., examples=["https://example.com/uploads/icons/premier-league-icon.png"])
    webview: str = Field(..., examples=["https://example.com/web/premier-league.png"])


class TournamentSchema(TournamentSchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., examples=[1])


class PaginatedTeamResponse(BaseModel):
    data: list[TeamSchema]
    metadata: PaginationMetadata


class TournamentWithDetailsSchema(TournamentSchema):
    season: SeasonSchema | None = Field(None, description="Season with full details")
    sport: SportSchema | None = Field(None, description="Sport with full details")
    teams: list[TeamSchema] = Field(default_factory=list, description="Teams in this tournament")
    main_sponsor: SponsorSchema | None = Field(None, description="Main sponsor with full details")
    sponsor_line: SponsorLineSchema | None = Field(
        None, description="Sponsor line with full details"
    )


class PaginatedTournamentWithDetailsResponse(BaseModel):
    data: list[TournamentWithDetailsSchema]
    metadata: PaginationMetadata
