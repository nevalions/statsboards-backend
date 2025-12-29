from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .match import MatchDB


class MatchDataDB(Base):
    __tablename__ = "matchdata"
    __table_args__ = {"extend_existing": True}

    field_length: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=92,
    )

    score_team_a: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=0,
    )
    score_team_b: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=0,
    )

    game_status: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        default="in-progress",
    )

    timeout_team_a: Mapped[str] = mapped_column(
        String(4),
        nullable=True,
        default="●●●",
    )

    timeout_team_b: Mapped[str] = mapped_column(
        String(4),
        nullable=True,
        default="●●●",
    )

    qtr: Mapped[str] = mapped_column(
        String(10),
        nullable=True,
        default="1st",
    )

    ball_on: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=20,
    )

    down: Mapped[str] = mapped_column(
        String(10),
        nullable=True,
        default="1st",
    )

    distance: Mapped[str] = mapped_column(
        String(20),
        nullable=True,
        default="10",
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
        back_populates="match_data",
    )
