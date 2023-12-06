from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

# from . import SeasonRelationMixin


if TYPE_CHECKING:
    from .season import SeasonDB
    from .tournament import TournamentDB


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

    #
    tournaments = relationship(
        "TournamentDB",
        secondary="team_tournament",
        back_populates="teams",
        cascade="save-update, merge",
    )


#
#     matches = relationship(
#         'MatchDB',
#         primaryjoin="or_(TeamDB.id==MatchDB.fk_team_a, TeamDB.id==MatchDB.fk_team_b)",
#         back_populates='teams', overlaps="team_a_matches, team_b_matches")
#
