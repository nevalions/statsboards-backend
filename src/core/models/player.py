from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .person import PersonDB
    from .sport import SportDB
    from .player_team_tournament import PlayerTeamTournamentDB
    from .team_tournament import TeamTournamentDB


class PlayerDB(Base):
    __tablename__ = "player"
    __table_args__ = {"extend_existing": True}

    sport_id: Mapped[int] = mapped_column(
        ForeignKey(
            "sport.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    person_id: Mapped[int] = mapped_column(
        ForeignKey(
            "person.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    player_eesl_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        unique=True,
    )

    person: Mapped["PersonDB"] = relationship(
        "PersonDB",
        back_populates="player",
    )

    sport: Mapped["SportDB"] = relationship(
        "SportDB",
        back_populates="players",
    )

    player_team_tournament: Mapped["PlayerTeamTournamentDB"] = relationship(
        "PlayerTeamTournamentDB",
        cascade="all, delete-orphan",
        back_populates="player",
        passive_deletes=True,
    )
