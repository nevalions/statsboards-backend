from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .player_team_tournament import PlayerTeamTournamentDB
    from .position import PositionDB
    from .match import MatchDB
    from .team import TeamDB


class PlayerMatchDB(Base):
    __tablename__ = "player_match"
    __table_args__ = {"extend_existing": True}

    player_match_eesl_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        unique=True,
    )

    player_team_tournament_id: Mapped[int] = mapped_column(
        ForeignKey(
            "player_team_tournament.id",
            ondelete="SET NULL",
        ),
        nullable=True,
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

    team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "team.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    match_position_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "position.id",
            ondelete="SET NULL",
        ),
        nullable=True,

    )

    match_number: Mapped[str] = mapped_column(
        String(10),
        nullable=True,
        default="0",
        server_default="0",
    )

    match_position: Mapped["PositionDB"] = relationship(
        "PositionDB",
        back_populates="match_players",
    )

    match: Mapped["MatchDB"] = relationship(
        "MatchDB",
        back_populates="match_players",
    )

    player_team_tournament: Mapped["PlayerTeamTournamentDB"] = relationship(
        "PlayerTeamTournamentDB",
        back_populates="player_match",
    )

    team: Mapped["TeamDB"] = relationship(
        "TeamDB",
        back_populates="match_players",
    )
