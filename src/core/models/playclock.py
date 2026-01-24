from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .match import MatchDB


class PlayClockDB(Base):
    __tablename__ = "playclock"
    __table_args__ = {"extend_existing": True}

    playclock: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    playclock_status: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        default="stopped",
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
        back_populates="match_playclock",
    )
