from __future__ import annotations

from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import make_fields_optional


class GameClockSchemaBase(BaseModel):
    gameclock: Annotated[int, Path(max=10000)] = 720
    gameclock_max: int | None = 720
    gameclock_status: Annotated[str, Path(max_length=50)] = "stopped"
    gameclock_time_remaining: int | None = None
    match_id: int | None = None
    version: Annotated[int, Path(ge=1)] = 1


# WebSocket Message Format for gameclock-update:
# {
#   "type": "gameclock-update",
#   "match_id": int,
#   "gameclock": {
#     "id": int,
#     "match_id": int,
#     "version": int,
#     "gameclock": int,
#     "gameclock_max": int | None,
#     "gameclock_status": str,
#     "gameclock_time_remaining": int | None
#   }
# }


GameClockSchemaUpdate = make_fields_optional(GameClockSchemaBase)


class GameClockSchemaCreate(GameClockSchemaBase):
    pass


class GameClockSchema(GameClockSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
