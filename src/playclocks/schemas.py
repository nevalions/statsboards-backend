from __future__ import annotations

from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import make_fields_optional


class PlayClockSchemaBase(BaseModel):
    playclock: Annotated[int, Path(max=10000)] | None = None
    playclock_status: Annotated[str, Path(max_length=50)] = "stopped"
    match_id: int | None = None
    version: Annotated[int, Path(ge=1)] = 1


# WebSocket Message Format for playclock-update:
# {
#   "type": "playclock-update",
#   "match_id": int,
#   "playclock": {
#     "id": int,
#     "match_id": int,
#     "version": int,
#     "playclock": int | None,
#     "playclock_status": str
#   }
# }


PlayClockSchemaUpdate = make_fields_optional(PlayClockSchemaBase)


class PlayClockSchemaCreate(PlayClockSchemaBase):
    pass


class PlayClockSchema(PlayClockSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
