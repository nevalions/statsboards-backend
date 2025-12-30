from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict


class SeasonSchemaBase(BaseModel):
    year: Annotated[
        int,
        Path(
            ge=1900,
            lt=3000,
        ),
    ]
    description: str | None = None


class SeasonSchemaUpdate(BaseModel):
    year: int | None = None
    description: str | None = None


class SeasonSchemaCreate(SeasonSchemaBase):
    pass


class SeasonSchema(SeasonSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
