from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .match import MatchDB


class ScoreboardDB(Base):
    __tablename__ = "scoreboard"
    __table_args__ = {"extend_existing": True}

    is_qtr: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    scale_logo_a: Mapped[int] = mapped_column(
        Float,
        nullable=True,
        default=2.0,
    )

    scale_logo_b: Mapped[int] = mapped_column(
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

    match_id = mapped_column(
        Integer,
        ForeignKey(
            "match.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        unique=True,
    )

    matches: Mapped["MatchDB"] = relationship(
        "MatchDB",
        back_populates="match_scoreboard",
    )
