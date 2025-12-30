from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .player import PlayerDB
    from .position import PositionDB
    from .team import TeamDB
    from .tournament import TournamentDB


class SportDB(Base):
    __tablename__ = "sport"
    __table_args__ = {"extend_existing": True}

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default="",
        server_default="",
    )

    tournaments: Mapped[list["TournamentDB"]] = relationship(
        back_populates="sport",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    players: Mapped[list["PlayerDB"]] = relationship(
        back_populates="sport",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    teams: Mapped[list["TeamDB"]] = relationship(
        back_populates="sport",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    positions: Mapped[list["PositionDB"]] = relationship(
        back_populates="sport",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
