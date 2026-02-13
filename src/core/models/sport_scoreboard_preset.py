from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import (
    ClockDirection,
    ClockOnStopBehavior,
    InitialTimeMode,
    PeriodClockVariant,
    SportPeriodMode,
)
from src.core.models import Base

if TYPE_CHECKING:
    from .sport import SportDB


class SportScoreboardPresetDB(Base):
    __tablename__ = "sport_scoreboard_preset"
    __table_args__ = {"extend_existing": True}

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Gameclock defaults
    gameclock_max: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=720,
    )
    initial_time_mode: Mapped[InitialTimeMode] = mapped_column(
        String(10),
        nullable=False,
        default=InitialTimeMode.MAX,
    )
    initial_time_min_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )
    period_clock_variant: Mapped[PeriodClockVariant] = mapped_column(
        String(10),
        nullable=False,
        default=PeriodClockVariant.PER_PERIOD,
    )
    direction: Mapped[ClockDirection] = mapped_column(
        String(10),
        nullable=False,
        default=ClockDirection.DOWN,
    )
    on_stop_behavior: Mapped[ClockOnStopBehavior] = mapped_column(
        String(10),
        nullable=False,
        default=ClockOnStopBehavior.HOLD,
    )

    # Scoreboard defaults
    has_playclock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    has_timeouts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_qtr: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_time: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_playclock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_downdistance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    has_timeouts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    has_playclock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    period_mode: Mapped[SportPeriodMode] = mapped_column(
        String(10),
        nullable=False,
        default=SportPeriodMode.QTR,
    )
    period_count: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    period_labels_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    default_playclock_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    sports: Mapped[list["SportDB"]] = relationship(
        back_populates="scoreboard_preset",
        passive_deletes=True,
    )
