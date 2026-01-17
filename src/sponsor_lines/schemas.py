from __future__ import annotations

from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import make_fields_optional


class SponsorLineSchemaBase(BaseModel):
    title: Annotated[str, Path(max_length=50)] = "Sponsor Line"
    is_visible: bool | None = False


SponsorLineSchemaUpdate = make_fields_optional(SponsorLineSchemaBase)


class SponsorLineSchemaCreate(SponsorLineSchemaBase):
    pass


class SponsorLineSchema(SponsorLineSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
