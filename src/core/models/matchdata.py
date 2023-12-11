from typing import TYPE_CHECKING
from datetime import datetime as date_type

from sqlalchemy import String, Integer, Text, TIMESTAMP, ForeignKey, TIME, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .match import MatchDB


class MatchDataDB(Base):
    __tablename__ = "matchdata"
    __table_args__ = {"extend_existing": True}

    score_team_a: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=0,
    )
    score_team_b = mapped_column(
        Integer,
        nullable=True,
        default=0,
    )
    match_id = mapped_column(
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
