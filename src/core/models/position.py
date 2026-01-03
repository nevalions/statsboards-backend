from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .player_match import PlayerMatchDB
    from .player_team_tournament import PlayerTeamTournamentDB
    from .sport import SportDB


class PositionDB(Base):
    __tablename__ = "position"
    __table_args__ = {"extend_existing": True}

    title: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    category: Mapped[str | None] = mapped_column(
        String(50),
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
        back_populates="positions",
    )

    players: Mapped[list["PlayerTeamTournamentDB"]] = relationship(
        back_populates="position",
    )

    match_players: Mapped[list["PlayerMatchDB"]] = relationship(
        back_populates="match_position",
    )
