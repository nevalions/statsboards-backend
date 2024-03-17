from fastapi import Path
from pydantic import BaseModel, ConfigDict
from typing import Annotated


class GameClockSchemaBase(BaseModel):
    gameclock: Annotated[int, Path(max=10000)] = 720
    gameclock_status: Annotated[str, Path(max_length=50)] = "stopped"
    match_id: int | None = None


class GameClockSchemaUpdate(BaseModel):
    gameclock: int | None = None
    gameclock_status: str | None = None
    match_id: int | None = None


class GameClockSchemaCreate(GameClockSchemaBase):
    pass


class GameClockSchema(GameClockSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
