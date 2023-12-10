from typing import TYPE_CHECKING
from datetime import datetime as date_type

from sqlalchemy import String, Integer, Text, TIMESTAMP, ForeignKey, TIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .team import TeamDB
    from .tournament import TournamentDB


class MatchDB(Base):
    __tablename__ = "match"
    __table_args__ = {"extend_existing": True}

    match_eesl_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        unique=True,
    )
    field_length: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=92,
    )
    match_date: Mapped[date_type] = mapped_column(
        TIME,
        nullable=True,
        default=date_type.now,
    )

    team_a_id: Mapped[int] = mapped_column(
        ForeignKey(
            "team.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    team_b_id: Mapped[int] = mapped_column(
        ForeignKey(
            "team.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey(
            "tournament.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    tournaments: Mapped["TournamentDB"] = relationship(
        "TournamentDB",
        back_populates="matches",
    )

    teams: Mapped["TeamDB"] = relationship(
        "TeamDB",
        back_populates="matches",
        primaryjoin="or_(TeamDB.id==MatchDB.team_a_id, TeamDB.id==MatchDB.team_b_id)",
        # overlaps="team_a_matches, team_b_matches",
    )

#     results = relationship('MatchResultDB', cascade="all, delete-orphan",
#                            back_populates="matches", passive_deletes=True)
#
#     fk_match_players_id = relationship('PlayerTeamTournamentDB',
#                                        secondary='player_match',
#                                        back_populates='fk_matches_id',
#                                        cascade="save-update, merge",
#                                        )
