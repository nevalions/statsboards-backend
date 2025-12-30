from fastapi import Path
from pydantic import BaseModel, ConfigDict
from typing import Annotated


class PositionSchemaBase(BaseModel):
    title: Annotated[str, Path(max_length=30)] = "Position"
    sport_id: int


class PositionSchemaUpdate(BaseModel):
    title: str | None = None
    sport_id: int | None = None


class PositionSchemaCreate(PositionSchemaBase):
    pass


class PositionSchema(PositionSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
