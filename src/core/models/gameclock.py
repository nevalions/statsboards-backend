from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import ClockDirection, ClockOnStopBehavior, ClockStatus
from src.core.models import Base

if TYPE_CHECKING:
    from .match import MatchDB


class GameClockDB(Base):
    __tablename__ = "gameclock"
    __table_args__ = {"extend_existing": True}

    gameclock_time_remaining: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    gameclock: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    gameclock_max: Mapped[int] = mapped_column(
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

    gameclock_status: Mapped[ClockStatus] = mapped_column(
        String(50),
        nullable=True,
        default=ClockStatus.STOPPED,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    started_at_ms: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        default=None,
    )

    use_sport_preset: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    match_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "match.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    matches: Mapped["MatchDB"] = relationship(
        "MatchDB",
        back_populates="match_gameclock",
    )
