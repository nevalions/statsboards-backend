from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import SportPeriodMode
from src.core.models import Base

if TYPE_CHECKING:
    from .match import MatchDB
    from .player_match import PlayerMatchDB


class ScoreboardDB(Base):
    __tablename__ = "scoreboard"
    __table_args__ = {"extend_existing": True}

    use_sport_preset: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_qtr: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    period_mode: Mapped[SportPeriodMode] = mapped_column(
        String(10),
        nullable=False,
        default=SportPeriodMode.QTR,
        server_default="qtr",
    )

    period_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=4,
        server_default="4",
    )

    period_labels_json: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    is_time: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_playclock: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_downdistance: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_tournament_logo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_main_sponsor: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_team_a_start_offense: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    is_team_b_start_offense: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    is_team_a_start_defense: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    is_team_b_start_defense: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    is_home_match_team_lower: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    is_away_match_team_lower: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    is_football_qb_full_stats_lower: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )
    is_match_player_lower: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    is_sponsor_line: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_match_sponsor_line: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=True,
    )

    language_code: Mapped[str | None] = mapped_column(
        String(5),
        nullable=True,
        default="en",
        server_default="en",
    )

    team_a_game_color: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="#c01c28",
        server_default="#c01c28",
    )

    use_team_a_game_color: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    team_b_game_color: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="#1c71d8",
        server_default="#1c71d8",
    )

    use_team_b_game_color: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    team_a_game_title: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )

    use_team_a_game_title: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    team_b_game_title: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )

    use_team_b_game_title: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    team_a_game_logo: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )

    use_team_a_game_logo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    team_b_game_logo: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )

    use_team_b_game_logo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    scale_tournament_logo: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        default=2.0,
    )

    scale_main_sponsor: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        default=2.0,
    )

    scale_logo_a: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        default=2.0,
    )

    scale_logo_b: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        default=2.0,
    )

    is_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    is_goal_team_a: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    is_goal_team_b: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    is_timeout_team_a: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    is_timeout_team_b: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    match_id = mapped_column(
        Integer,
        ForeignKey(
            "match.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        unique=True,
    )

    player_match_lower_id = mapped_column(
        Integer,
        ForeignKey(
            "player_match.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    football_qb_full_stats_match_lower_id = mapped_column(
        Integer,
        ForeignKey(
            "player_match.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    matches: Mapped["MatchDB"] = relationship(
        "MatchDB",
        back_populates="match_scoreboard",
    )

    # match_players: Mapped["PlayerMatchDB"] = relationship(
    #     "PlayerMatchDB",
    #     back_populates="match_scoreboard",
    # )

    match_player_match_lower_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="ScoreboardDB.player_match_lower_id == PlayerMatchDB.id",
        back_populates="match_player_lower",
    )

    match_football_qb_full_stats_match_lower_rel: Mapped["PlayerMatchDB"] = relationship(
        "PlayerMatchDB",
        primaryjoin="ScoreboardDB.football_qb_full_stats_match_lower_id == PlayerMatchDB.id",
        back_populates="football_qb_full_stats_match_player_lower",
    )
