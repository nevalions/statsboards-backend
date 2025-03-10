from datetime import datetime as date_type
from typing import TYPE_CHECKING

from sqlalchemy import Integer, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .team import TeamDB
    from .tournament import TournamentDB
    from .matchdata import MatchDataDB
    from .sponsor import SponsorDB
    from .sponsor_line import SponsorLineDB
    from .scoreboard import ScoreboardDB
    from .playclock import PlayClockDB
    from .gameclock import GameClockDB
    from .player_match import PlayerMatchDB
    from .football_event import FootballEventDB


class MatchDB(Base):
    __tablename__ = "match"
    __table_args__ = {"extend_existing": True}

    match_date: Mapped[date_type] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, server_default=func.now()
    )

    week: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=1,
    )

    match_eesl_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        unique=True,
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

    main_sponsor_id: Mapped[int] = mapped_column(
        ForeignKey("sponsor.id"),
        nullable=True,
    )

    sponsor_line_id: Mapped[int] = mapped_column(
        ForeignKey("sponsor_line.id"),
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
    )

    main_sponsor: Mapped["SponsorDB"] = relationship(
        "SponsorDB",
        back_populates="matches",
    )

    sponsor_line: Mapped["SponsorLineDB"] = relationship(
        "SponsorLineDB",
        back_populates="matches",
    )

    match_data: Mapped["MatchDataDB"] = relationship(
        "MatchDataDB",
        cascade="all, delete-orphan",
        back_populates="matches",
        passive_deletes=True,
    )

    match_playclock: Mapped["PlayClockDB"] = relationship(
        "PlayClockDB",
        cascade="all, delete-orphan",
        back_populates="matches",
        passive_deletes=True,
    )

    match_gameclock: Mapped["GameClockDB"] = relationship(
        "GameClockDB",
        cascade="all, delete-orphan",
        back_populates="matches",
        passive_deletes=True,
    )

    match_scoreboard: Mapped["ScoreboardDB"] = relationship(
        "ScoreboardDB",
        cascade="all, delete-orphan",
        back_populates="matches",
        passive_deletes=True,
    )

    match_players: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        cascade="all, delete-orphan",
        back_populates="match",
        passive_deletes=True,
    )

    match_events: Mapped["FootballEventDB"] = relationship(
        "FootballEventDB",
        cascade="all, delete-orphan",
        back_populates="matches",
        passive_deletes=True,
    )


#
#     fk_match_players_id = relationship('PlayerTeamTournamentDB',
#                                        secondary='player_match',
#                                        back_populates='fk_matches_id',
#                                        cascade="save-update, merge",
#                                        )
