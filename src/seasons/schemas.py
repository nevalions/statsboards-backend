from __future__ import annotations

from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import make_fields_optional


class SeasonSchemaBase(BaseModel):
    year: Annotated[
        int,
        Path(
            ge=1900,
            lt=3000,
        ),
    ]
    description: str | None = None
    iscurrent: bool = False


SeasonSchemaUpdate = make_fields_optional(SeasonSchemaBase)


class SeasonSchemaCreate(SeasonSchemaBase):
    pass


class SeasonSchema(SeasonSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
