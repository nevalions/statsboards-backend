from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .player import PlayerDB
    from .player_match import PlayerMatchDB
    from .position import PositionDB
    from .team import TeamDB
    from .tournament import TournamentDB


class PlayerTeamTournamentDB(Base):
    __tablename__ = "player_team_tournament"
    __table_args__ = {"extend_existing": True}

    player_team_tournament_eesl_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        unique=True,
    )

    player_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "player.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "team.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    position_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "position.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    team: Mapped["TeamDB"] = relationship(
        "TeamDB",
        back_populates="players_team_tournament",
    )

    tournament: Mapped["TournamentDB"] = relationship(
        "TournamentDB",
        back_populates="players_team_tournament",
    )

    player_number: Mapped[str] = mapped_column(
        String(10),
        nullable=True,
        default="0",
        server_default="0",
    )

    position: Mapped["PositionDB"] = relationship(
        "PositionDB",
        back_populates="players",
    )

    player: Mapped["PlayerDB"] = relationship(
        "PlayerDB",
        cascade="all, delete-orphan",
        back_populates="player_team_tournament",
        passive_deletes=True,
    )

    player_match: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatch",
        cascade="all, delete-orphan",
        back_populates="player_team_tournament",
        passive_deletes=True,
    )

    person: Mapped["PersonDB"] = relationship(
        "PersonDB",
        lazy="joined",
        back_populates="players_team_tournament",
    )

    player_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "player.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "team.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    position_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "position.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    team: Mapped["TeamDB"] = relationship(
        "TeamDB",
        back_populates="players_team_tournament",
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
        back_populates="players_team_tournament",
    )

    player_number: Mapped[str] = mapped_column(
        String(10),
        nullable=True,
        default="0",
        server_default="0",
    )

    position: Mapped["PositionDB"] = relationship(
        "PositionDB",
        back_populates="players",
    )

    player: Mapped["PlayerDB"] = relationship(
        "PlayerDB",
        back_populates="players_team_tournament",
        lazy="joined",
    )

    player_match: Mapped["PlayerMatchDB"] = relationship(
        "PlayerDB",
        cascade="all, delete-orphan",
        back_populates="player_team_tournament",
        passive_deletes=True,
    )

    #
    # player_position: Mapped[str] = mapped_column(
    #     String(20),
    #     nullable=True,
    #     default="",
    #     server_default="",
    # )
