from __future__ import annotations

from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import make_fields_optional


class PositionSchemaBase(BaseModel):
    title: Annotated[str, Path(max_length=30)] = "Position"
    sport_id: int


PositionSchemaUpdate = make_fields_optional(PositionSchemaBase)


class PositionSchemaCreate(PositionSchemaBase):
    pass


class PositionSchema(PositionSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
