from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
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
