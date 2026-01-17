from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, Field


class PlayerTeamTournamentBaseFields(BaseModel):
    """Base fields shared across player team tournament related schemas"""

    player_team_tournament_eesl_id: int | None = None
    player_id: int
    player_number: Annotated[str, Path(max_length=10)] | None = "0"
    team_id: int | None = None
    tournament_id: int | None = None
    position_id: int | None = None


class PlayerTeamTournamentWithTitles(BaseModel):
    """Base fields including related title fields"""

    id: int
    player_team_tournament_eesl_id: int | None = None
    player_number: Annotated[str, Path(max_length=10)] | None = "0"
    team_id: int | None = None
    team_title: str | None = None
    position_id: int | None = None
    position_title: str | None = None
    tournament_id: int | None = None


class SponsorFieldsBase(BaseModel):
    """Base fields for sponsor relationships"""

    sponsor_line_id: int | None = Field(None, examples=[1])
    main_sponsor_id: int | None = Field(None, examples=[5])


class PrivacyFieldsBase(BaseModel):
    """Base fields for privacy and ownership"""

    isprivate: bool = Field(False, examples=[False, True])
    user_id: int | None = Field(None, examples=[1])


class LogoFieldsBase(BaseModel):
    """Base fields for logo/photo URLs with original, icon, and web variants"""

    original_url: Annotated[str, Path(max_length=500)] | None = ""
    icon_url: Annotated[str, Path(max_length=500)] | None = ""
    webview_url: Annotated[str, Path(max_length=500)] | None = ""
