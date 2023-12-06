from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .tournament import TournamentDB


class SeasonDB(Base):
    __tablename__ = "season"
    __table_args__ = {"extend_existing": True}

    year: Mapped[int] = mapped_column(
        Integer,
        unique=True,
    )
    description: Mapped[int] = mapped_column(
        Text,
        nullable=True,
        default="",
        server_default="",
    )

    tournaments: Mapped[list["TournamentDB"]] = relationship(
        back_populates="season",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def get_tournaments(self):
        return self.tournaments

    # tournaments = relationship(
    #     'TournamentDB', cascade="all, delete-orphan", back_populates="seasons",
    #     passive_deletes=True)
