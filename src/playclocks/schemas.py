from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict


class PlayClockSchemaBase(BaseModel):
    playclock: Annotated[int, Path(max=10000)] | None = None
    playclock_status: Annotated[str, Path(max_length=50)] = "stopped"
    match_id: int | None = None


class PlayClockSchemaUpdate(BaseModel):
    playclock: int | None = None
    playclock_status: str | None = None

    match_id: int | None = None


class PlayClockSchemaCreate(PlayClockSchemaBase):
    pass


class PlayClockSchema(PlayClockSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
