from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.models import Base

if TYPE_CHECKING:
    from .player import PlayerDB
    from .player_team_tournament import PlayerTeamTournamentDB


class TeamTournamentDB(Base):
    __tablename__ = "team_tournament"
    __table_args__ = (
        UniqueConstraint(
            "tournament_id",
            "team_id",
            name="idx_unique_team_tournament",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "tournament.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "team.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )


# fk_players_id = relationship('PlayerDB',
#                              secondary='player_team_tournament',
#                              back_populates='fk_team_tournaments_id',
#                              cascade="save-update, merge",
#                              )
