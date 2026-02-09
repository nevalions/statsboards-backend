from __future__ import annotations

from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

from src.core.enums import ClockDirection, ClockOnStopBehavior
from src.core.schema_helpers import make_fields_optional


class SportScoreboardPresetSchemaBase(BaseModel):
    title: Annotated[str, Path(max_length=255)]
    gameclock_max: int | None = 720
    direction: Annotated[ClockDirection, Path(max_length=10)] = ClockDirection.DOWN
    on_stop_behavior: Annotated[ClockOnStopBehavior, Path(max_length=10)] = ClockOnStopBehavior.HOLD
    is_qtr: bool = True
    is_time: bool = True
    is_playclock: bool = True
    is_downdistance: bool = True


SportScoreboardPresetSchemaUpdate = make_fields_optional(SportScoreboardPresetSchemaBase)


class SportScoreboardPresetSchemaCreate(SportScoreboardPresetSchemaBase):
    pass


class SportScoreboardPresetSchema(SportScoreboardPresetSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
