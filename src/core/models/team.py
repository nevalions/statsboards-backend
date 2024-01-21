from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base


if TYPE_CHECKING:
    from .tournament import TournamentDB
    from .match import MatchDB
    from .sport import SportDB


class TeamDB(Base):
    __tablename__ = "team"
    __table_args__ = {"extend_existing": True}

    team_eesl_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        unique=True,
    )
    title: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default="",
        server_default="",
    )
    team_logo_url: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )

    sport_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "sport.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    sport: Mapped["SportDB"] = relationship(
        "SportDB",
        back_populates="teams",
    )

    tournaments: Mapped[list["TournamentDB"]] = relationship(
        secondary="team_tournament",
        back_populates="teams",
        cascade="save-update, merge",
    )

    matches: Mapped["MatchDB"] = relationship(
        "MatchDB",
        primaryjoin="or_(TeamDB.id==MatchDB.team_a_id, TeamDB.id==MatchDB.team_b_id)",
        back_populates="teams",
    )
