from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .tournament import TournamentDB


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

    tournaments: Mapped["TournamentDB"] = relationship(
        "TournamentDB",
        back_populates="main_sponsor",
    )
