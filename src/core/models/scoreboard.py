from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .match import MatchDB


class ScoreboardDB(Base):
    __tablename__ = "scoreboard"
    __table_args__ = {"extend_existing": True}

    is_qtr: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_time: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_playclock: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_downdistance: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    team_a_color: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="#c01c28",
        server_default="#c01c28",
    )

    team_b_color: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="#1c71d8",
        server_default="#1c71d8",
    )

    match_id = mapped_column(
        Integer,
        ForeignKey(
            "match.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        unique=True,
    )

    matches: Mapped["MatchDB"] = relationship(
        "MatchDB",
        back_populates="match_scoreboard",
    )
