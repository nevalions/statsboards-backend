from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .player_team_tournament import PlayerTeamTournamentDB
    from .position import PositionDB
    from .match import MatchDB
    from .team import TeamDB
    from .scoreboard import ScoreboardDB
    from .football_event import FootballEventDB


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
    )

    team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "team.id",
            ondelete="CASCADE",
        ),
        nullable=False,
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

    is_start: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
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

    # match_scoreboard: Mapped["ScoreboardDB"] = relationship(
    #     "ScoreboardDB",
    #     back_populates="match_players",
    # )

    match_player_lower: Mapped[list["ScoreboardDB"]] = relationship(
        "ScoreboardDB",
        foreign_keys="ScoreboardDB.player_match_lower_id",
        back_populates="match_player_match_lower_rel",
    )

    football_qb_full_stats_match_player_lower: Mapped[
        list["ScoreboardDB"]
    ] = relationship(
        "ScoreboardDB",
        foreign_keys="ScoreboardDB.football_qb_full_stats_match_lower_id",
        back_populates="match_football_qb_full_stats_match_lower_rel",
    )

    event_qb_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.event_qb",
        back_populates="event_qb_rel",
    )

    run_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.run_player",
        back_populates="run_player_rel",
    )

    pass_received_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.pass_received_player",
        back_populates="pass_received_player_rel",
    )

    pass_dropped_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.pass_dropped_player",
        back_populates="pass_dropped_player_rel",
    )

    pass_deflected_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.pass_deflected_player",
        back_populates="pass_deflected_player_rel",
    )

    pass_intercepted_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.pass_intercepted_player",
        back_populates="pass_intercepted_player_rel",
    )

    fumble_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.fumble_player",
        back_populates="fumble_player_rel",
    )

    fumble_recovered_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.fumble_recovered_player",
        back_populates="fumble_recovered_player_rel",
    )

    tackle_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.tackle_player",
        back_populates="tackle_player_rel",
    )

    assist_tackle_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.assist_tackle_player",
        back_populates="assist_tackle_player_rel",
    )

    sack_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.sack_player",
        back_populates="sack_player_rel",
    )

    score_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.score_player",
        back_populates="score_player_rel",
    )

    defence_score_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.defence_score_player",
        back_populates="defence_score_player_rel",
    )

    kick_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.kick_player",
        back_populates="kick_player_rel",
    )

    kickoff_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.kickoff_player",
        back_populates="kickoff_player_rel",
    )
    return_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.return_player",
        back_populates="return_player_rel",
    )
    pat_one_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.pat_one_player",
        back_populates="pat_one_player_rel",
    )
    flagged_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.flagged_player",
        back_populates="flagged_player_rel",
    )

    punt_player_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        foreign_keys="FootballEventDB.punt_player",
        back_populates="punt_player_rel",
    )
