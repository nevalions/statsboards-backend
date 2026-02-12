from __future__ import annotations

import re
from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict, model_validator

from src.core.enums import (
    ClockDirection,
    ClockOnStopBehavior,
    InitialTimeMode,
    SportPeriodMode,
)
from src.core.schema_helpers import make_fields_optional

MACHINE_LABEL_KEY_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")


class SportScoreboardPresetSchemaBase(BaseModel):
    title: Annotated[str, Path(max_length=255)]
    gameclock_max: int | None = 720
    initial_time_mode: Annotated[InitialTimeMode, Path(max_length=10)] = InitialTimeMode.MAX
    initial_time_min_seconds: int | None = None
    direction: Annotated[ClockDirection, Path(max_length=10)] = ClockDirection.DOWN
    on_stop_behavior: Annotated[ClockOnStopBehavior, Path(max_length=10)] = ClockOnStopBehavior.HOLD
    is_qtr: bool = True
    is_time: bool = True
    is_playclock: bool = True
    is_downdistance: bool = True
    has_timeouts: bool = True
    has_playclock: bool = True
    period_mode: Annotated[SportPeriodMode, Path(max_length=10)] = SportPeriodMode.QTR
    period_count: Annotated[int, Path(ge=1, le=99)] = 4
    period_labels_json: list[str] | None = None
    default_playclock_seconds: int | None = None

    @model_validator(mode="after")
    def validate_period_labels(self) -> SportScoreboardPresetSchemaBase:
        if self.initial_time_mode == InitialTimeMode.MIN and self.initial_time_min_seconds is None:
            raise ValueError("initial_time_min_seconds is required when initial_time_mode='min'")

        if self.period_labels_json is None:
            return self

        if self.period_mode != SportPeriodMode.CUSTOM:
            raise ValueError("period_labels_json is allowed only when period_mode='custom'")

        invalid_labels = [
            label
            for label in self.period_labels_json
            if not MACHINE_LABEL_KEY_PATTERN.fullmatch(label)
        ]
        if invalid_labels:
            raise ValueError(
                "period_labels_json must contain stable machine-friendly keys "
                "(lowercase letters/numbers with '.', '_' or '-')"
            )

        if self.period_count != len(self.period_labels_json):
            raise ValueError(
                "period_count must match period_labels_json length when period_mode='custom'"
            )

        return self


SportScoreboardPresetSchemaUpdate = make_fields_optional(SportScoreboardPresetSchemaBase)


class SportScoreboardPresetSchemaCreate(SportScoreboardPresetSchemaBase):
    pass


class SportScoreboardPresetSchema(SportScoreboardPresetSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
