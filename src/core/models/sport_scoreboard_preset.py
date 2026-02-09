from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import ClockDirection, ClockOnStopBehavior
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
    is_qtr: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_time: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_playclock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_downdistance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    sports: Mapped[list["SportDB"]] = relationship(
        back_populates="scoreboard_preset",
        passive_deletes=True,
    )
