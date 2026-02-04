from __future__ import annotations

from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import PaginationMetadata


class SponsorLineSchemaBase(BaseModel):
    title: Annotated[str, Path(max_length=50)] = "Sponsor Line"
    is_visible: bool | None = False


class SponsorLineSchemaUpdate(BaseModel):
    title: Annotated[str | None, Path(max_length=50)] = None
    is_visible: bool | None = None


class SponsorLineSchemaCreate(SponsorLineSchemaBase):
    pass


class SponsorLineSchema(SponsorLineSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class PaginatedSponsorLineResponse(BaseModel):
    data: list[SponsorLineSchema]
    metadata: PaginationMetadata
