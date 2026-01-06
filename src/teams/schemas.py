from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict, Field

from src.core.schema_helpers import make_fields_optional, PaginationMetadata


class TeamSchemaBase(BaseModel):
    team_eesl_id: int | None = Field(None, examples=[12345])
    title: Annotated[str, Path(max_length=50)] = Field("Team", examples=["Manchester United"])
    city: Annotated[str, Path(max_length=50)] | None = Field("City", examples=["Manchester"])
    description: str | None = Field("", examples=["Premier League football club"])
    team_logo_url: Annotated[str, Path(max_length=500)] | None = Field(
        "", examples=["https://example.com/logos/manchester-united.png"]
    )
    team_logo_icon_url: Annotated[str, Path(max_length=500)] | None = Field(
        "", examples=["https://example.com/icons/manchester-united-icon.png"]
    )
    team_logo_web_url: Annotated[str, Path(max_length=500)] | None = Field(
        "", examples=["https://example.com/web/manchester-united.png"]
    )
    team_color: Annotated[str, Path(max_length=10)] = Field(
        "#c01c28", examples=["#DA291C", "#6CABDD"]
    )
    sponsor_line_id: int | None = Field(None, examples=[1])
    main_sponsor_id: int | None = Field(None, examples=[5])
    sport_id: int = Field(..., examples=[1])


TeamSchemaUpdate = make_fields_optional(TeamSchemaBase)


class TeamSchemaCreate(TeamSchemaBase):
    pass


class TeamSchema(TeamSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., examples=[1])


class UploadTeamLogoResponse(BaseModel):
    logoUrl: str = Field(..., examples=["https://example.com/uploads/logos/manchester-united.png"])


class UploadResizeTeamLogoResponse(BaseModel):
    original: str = Field(..., examples=["https://example.com/uploads/logos/manchester-united.png"])
    icon: str = Field(
        ..., examples=["https://example.com/uploads/icons/manchester-united-icon.png"]
    )
    webview: str = Field(..., examples=["https://example.com/uploads/web/manchester-united.png"])


class PaginatedTeamResponse(BaseModel):
    data: list[TeamSchema]
    metadata: PaginationMetadata
