from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .player import PlayerDB
    from .tournament import TournamentDB
    from .team import TeamDB


class PlayerTeamTournamentDB(Base):
    __tablename__ = "player_team_tournament"
    __table_args__ = {"extend_existing": True}

    player_team_tournament_eesl_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        unique=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey(
            "player.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    player: Mapped["PlayerDB"] = relationship(
        "PlayerDB",
        back_populates="player_team_tournament",
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey(
            "team.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    team: Mapped["TeamDB"] = relationship(
        "TeamDB",
        back_populates="player_team_tournament",
    )

    tournament_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "tournament.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    tournament: Mapped["TournamentDB"] = relationship(
        "TournamentDB",
        back_populates="player_team_tournament",
    )

    player_number: Mapped[str] = mapped_column(
        String(10),
        nullable=True,
        default="0",
        server_default="0",
    )

    player_position: Mapped[str] = mapped_column(
        String(20),
        nullable=True,
        default="",
        server_default="",
    )
