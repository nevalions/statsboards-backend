from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base
from . import SeasonSportRelationMixin

if TYPE_CHECKING:
    from .team import TeamDB
    from .match import MatchDB


class TournamentDB(SeasonSportRelationMixin, Base):
    __tablename__ = "tournament"
    __table_args__ = {"extend_existing": True}
    _season_id_nullable = False
    _sport_id_nullable = True
    _ondelete = "CASCADE"
    _season_back_populates = "tournaments"
    _sport_back_populates = "tournaments"

    tournament_eesl_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        unique=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default="",
        server_default="",
    )
    tournament_logo_url: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )

    teams: Mapped[list["TeamDB"]] = relationship(
        secondary="team_tournament",
        back_populates="tournaments",
    )

    matches: Mapped[list["MatchDB"]] = relationship(
        cascade="all, delete-orphan",
        back_populates="tournaments",
        passive_deletes=True,
    )
