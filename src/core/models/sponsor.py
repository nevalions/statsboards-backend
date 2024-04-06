from typing import TYPE_CHECKING

from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .tournament import TournamentDB
    from .team import TeamDB
    from .sponsor_line import SponsorLineDB


class SponsorDB(Base):
    __tablename__ = "sponsor"
    __table_args__ = {"extend_existing": True}

    title: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    logo_url: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        default="",
        server_default="",
    )
    scale_logo: Mapped[int] = mapped_column(
        Float,
        nullable=True,
        default=1.0,
    )

    tournaments: Mapped["TournamentDB"] = relationship(
        "TournamentDB",
        back_populates="main_sponsor",
    )

    teams: Mapped["TeamDB"] = relationship(
        "TeamDB",
        back_populates="main_sponsor",
    )

    sponsor_lines: Mapped[list["SponsorLineDB"]] = relationship(
        secondary="sponsor_sponsor_line",
        back_populates="sponsors",
        cascade="save-update, merge",
    )
