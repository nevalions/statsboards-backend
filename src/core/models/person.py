from typing import TYPE_CHECKING

from datetime import datetime as date_type
from sqlalchemy import String, TIMESTAMP, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .player import PlayerDB


class PersonDB(Base):
    __tablename__ = "person"
    __table_args__ = {"extend_existing": True}

    person_eesl_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        unique=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
        server_default="",
    )

    second_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
        server_default="",
    )

    person_photo_url: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        default="",
        server_default="",
    )

    person_dob: Mapped[date_type] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    player: Mapped["PlayerDB"] = relationship(
        "PlayerDB",
        cascade="all, delete-orphan",
        back_populates="person",
        passive_deletes=True,
    )
