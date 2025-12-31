from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict, Field


class TournamentSchemaBase(BaseModel):
    tournament_eesl_id: int | None = Field(None, examples=[67890])
    title: Annotated[str, Path(max_length=255)] = Field("Tournament", examples=["Premier League", "La Liga"])
    description: str | None = Field("", examples=["Top tier English football league"])
    tournament_logo_url: Annotated[str, Path(max_length=500)] | None = Field("", examples=["https://example.com/logos/premier-league.png"])
    tournament_logo_icon_url: Annotated[str, Path(max_length=500)] | None = Field("", examples=["https://example.com/icons/premier-league-icon.png"])
    tournament_logo_web_url: Annotated[str, Path(max_length=500)] | None = Field("", examples=["https://example.com/web/premier-league.png"])
    season_id: int = Field(..., examples=[1])
    sport_id: int = Field(..., examples=[1])
    sponsor_line_id: int | None = Field(None, examples=[1])
    main_sponsor_id: int | None = Field(None, examples=[5])


class TournamentSchemaUpdate(BaseModel):
    tournament_eesl_id: int | None = Field(None, examples=[67890])
    title: str | None = Field(None, examples=["Premier League", "La Liga"])
    description: str | None = Field(None, examples=["Top tier English football league"])
    tournament_logo_url: str | None = Field(None, examples=["https://example.com/logos/premier-league.png"])
    tournament_logo_icon_url: str | None = Field(None, examples=["https://example.com/icons/premier-league-icon.png"])
    tournament_logo_web_url: str | None = Field(None, examples=["https://example.com/web/premier-league.png"])
    season_id: int | None = Field(None, examples=[1])
    sport_id: int | None = Field(None, examples=[1])
    sponsor_line_id: int | None = Field(None, examples=[1])
    main_sponsor_id: int | None = Field(None, examples=[5])


class TournamentSchemaCreate(TournamentSchemaBase):
    pass


class UploadTournamentLogoResponse(BaseModel):
    logoUrl: str = Field(..., examples=["https://example.com/uploads/logos/premier-league.png"])


class UploadResizeTournamentLogoResponse(BaseModel):
    original: str = Field(..., examples=["https://example.com/uploads/logos/premier-league.png"])
    icon: str = Field(..., examples=["https://example.com/uploads/icons/premier-league-icon.png"])
    webview: str = Field(..., examples=["https://example.com/uploads/web/premier-league.png"])


class TournamentSchema(TournamentSchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., examples=[1])
