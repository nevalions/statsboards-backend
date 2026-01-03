from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import make_fields_optional


class SportSchemaBase(BaseModel):
    title: Annotated[str, Path(max_length=255)]
    description: str | None = None


SportSchemaUpdate = make_fields_optional(SportSchemaBase)


class SportSchemaCreate(SportSchemaBase):
    pass


class SportSchema(SportSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
