from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    gameclock_status: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        default="stopped",
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
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
