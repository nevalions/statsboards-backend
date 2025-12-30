from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .match import MatchDB
    from .player_match import PlayerMatchDB
    from .player_team_tournament import PlayerTeamTournamentDB
    from .sponsor import SponsorDB
    from .sponsor_line import SponsorLineDB
    from .sport import SportDB
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
    city: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default="",
        server_default="",
    )
    team_logo_url: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        default="",
        server_default="",
    )

    team_logo_icon_url: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        default="",
        server_default="",
    )

    team_logo_web_url: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        default="",
        server_default="",
    )

    team_color: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="#c01c28",
        server_default="#c01c28",
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
        back_populates="teams",
    )

    tournaments: Mapped[list["TournamentDB"]] = relationship(
        secondary="team_tournament",
        back_populates="teams",
        cascade="save-update, merge",
    )

    matches: Mapped["MatchDB"] = relationship(
        "MatchDB",
        primaryjoin="or_(TeamDB.id==MatchDB.team_a_id, TeamDB.id==MatchDB.team_b_id)",
        back_populates="teams",
    )

    sponsor_line_id: Mapped[int] = mapped_column(
        ForeignKey("sponsor_line.id"),
        nullable=True,
    )

    main_sponsor_id: Mapped[int] = mapped_column(
        ForeignKey("sponsor.id"),
        nullable=True,
    )

    main_sponsor: Mapped["SponsorDB"] = relationship(
        "SponsorDB",
        back_populates="teams",
    )

    sponsor_line: Mapped["SponsorLineDB"] = relationship(
        "SponsorLineDB",
        back_populates="teams",
    )

    players_team_tournament: Mapped["PlayerTeamTournamentDB"] = relationship(
        "PlayerTeamTournamentDB", cascade="all", back_populates="team"
    )

    match_players: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        cascade="all, delete-orphan",
        back_populates="team",
        passive_deletes=True,
    )
