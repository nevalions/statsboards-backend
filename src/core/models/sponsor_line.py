from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .sponsor import SponsorDB
    from .tournament import TournamentDB
    from .team import TeamDB


class SponsorLineDB(Base):
    __tablename__ = "sponsor_line"
    __table_args__ = {"extend_existing": True}

    title: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        default="Sponsor Line",
        server_default="Sponsor Line",
    )

    tournaments: Mapped["TournamentDB"] = relationship(
        "TournamentDB",
        back_populates="sponsor_line",
    )

    teams: Mapped["TeamDB"] = relationship(
        "TeamDB",
        back_populates="sponsor_line",
    )

    sponsors: Mapped[list["SponsorDB"]] = relationship(
        secondary="sponsor_sponsor_line",
        back_populates="sponsor_lines",
    )
