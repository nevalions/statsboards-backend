from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict


class SportSchemaBase(BaseModel):
    title: Annotated[str, Path(max_length=255)]
    description: str | None = None


class SportSchemaUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class SportSchemaCreate(SportSchemaBase):
    pass


class SportSchema(SportSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
