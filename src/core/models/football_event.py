from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .match import MatchDB
    from .player_match import PlayerMatchDB


class FootballEventDB(Base):
    __tablename__ = "football_event"
    __table_args__ = {"extend_existing": True}

    match_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "match.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    event_number: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    event_qtr: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    ball_on: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    ball_moved_to: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    ball_picked_on: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    ball_picked_on_fumble: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    ball_kicked_to: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    ball_returned_to: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    ball_returned_to_on_fumble: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    distance_on_offence: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    offense_team: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("team.id"),
        nullable=True,
        default=None,
    )

    event_qb: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    event_down: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    event_distance: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    event_strong_side: Mapped[str] = mapped_column(
        String,
        nullable=True,
        default=None,
    )

    event_hash: Mapped[str] = mapped_column(
        String,
        nullable=True,
        default=None,
    )

    play_direction: Mapped[str] = mapped_column(
        String,
        nullable=True,
        default=None,
    )

    play_type: Mapped[str] = mapped_column(
        String,
        nullable=True,
        default=None,
    )

    play_result: Mapped[str] = mapped_column(
        String,
        nullable=True,
        default=None,
    )

    score_result: Mapped[str] = mapped_column(
        String,
        nullable=True,
        default=None,
    )

    is_fumble: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    is_fumble_recovered: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    run_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    pass_received_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    pass_dropped_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    pass_deflected_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    pass_intercepted_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    fumble_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    fumble_recovered_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    tackle_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    assist_tackle_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    sack_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    score_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    defence_score_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    kick_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    kickoff_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    return_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    pat_one_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    flagged_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    punt_player: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("player_match.id"),
        nullable=True,
        default=None,
    )

    matches: Mapped["MatchDB"] = relationship(
        "MatchDB",
        back_populates="match_events",
    )

    event_qb_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.event_qb == PlayerMatchDB.id",
        back_populates="event_qb_events",
    )

    run_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.run_player == PlayerMatchDB.id",
        back_populates="run_player_events",
    )

    pass_received_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.pass_received_player == PlayerMatchDB.id",
        back_populates="pass_received_player_events",
    )

    pass_dropped_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.pass_dropped_player == PlayerMatchDB.id",
        back_populates="pass_dropped_player_events",
    )

    pass_deflected_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.pass_deflected_player == PlayerMatchDB.id",
        back_populates="pass_deflected_player_events",
    )

    pass_intercepted_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.pass_intercepted_player == PlayerMatchDB.id",
        back_populates="pass_intercepted_player_events",
    )

    fumble_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.fumble_player == PlayerMatchDB.id",
        back_populates="fumble_player_events",
    )

    fumble_recovered_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.fumble_recovered_player == PlayerMatchDB.id",
        back_populates="fumble_recovered_player_events",
    )

    tackle_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.tackle_player == PlayerMatchDB.id",
        back_populates="tackle_player_events",
    )

    assist_tackle_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.tackle_player == PlayerMatchDB.id",
        back_populates="assist_tackle_player_events",
    )

    sack_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.sack_player == PlayerMatchDB.id",
        back_populates="sack_player_events",
    )

    score_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.tackle_player == PlayerMatchDB.id",
        back_populates="score_player_events",
    )

    defence_score_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.tackle_player == PlayerMatchDB.id",
        back_populates="defence_score_player_events",
    )

    kick_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.kick_player == PlayerMatchDB.id",
        back_populates="kick_player_events",
    )

    kickoff_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.tackle_player == PlayerMatchDB.id",
        back_populates="kickoff_player_events",
    )
    return_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.tackle_player == PlayerMatchDB.id",
        back_populates="return_player_events",
    )
    pat_one_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.tackle_player == PlayerMatchDB.id",
        back_populates="pat_one_player_events",
    )
    flagged_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.tackle_player == PlayerMatchDB.id",
        back_populates="flagged_player_events",
    )

    punt_player_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="FootballEventDB.punt_player == PlayerMatchDB.id",
        back_populates="punt_player_events",
    )
