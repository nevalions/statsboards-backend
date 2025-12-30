from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .match import MatchDB
    from .sponsor import SponsorDB
    from .team import TeamDB
    from .tournament import TournamentDB


class SponsorLineDB(Base):
    __tablename__ = "sponsor_line"
    __table_args__ = {"extend_existing": True}

    title: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        default="Sponsor Line",
        server_default="Sponsor Line",
    )

    is_visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
    )

    tournaments: Mapped["TournamentDB"] = relationship(
        "TournamentDB",
        back_populates="sponsor_line",
    )

    teams: Mapped["TeamDB"] = relationship(
        "TeamDB",
        back_populates="sponsor_line",
    )

    matches: Mapped["MatchDB"] = relationship(
        "MatchDB",
        back_populates="sponsor_line",
    )

    sponsors: Mapped[list["SponsorDB"]] = relationship(
        secondary="sponsor_sponsor_line",
        back_populates="sponsor_lines",
    )
