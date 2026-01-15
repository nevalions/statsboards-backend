from datetime import datetime as date_type
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .player import PlayerDB
    from .user import UserDB


class PersonDB(Base):
    __tablename__ = "person"
    __table_args__ = {"extend_existing": True}

    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", name="fk_person_owner_user", ondelete="SET NULL"),
        nullable=True,
    )

    isprivate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

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

    person_photo_icon_url: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        default="",
        server_default="",
    )

    person_photo_web_url: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        default="",
        server_default="",
    )

    person_dob: Mapped[date_type] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    players: Mapped[list["PlayerDB"]] = relationship(
        "PlayerDB",
        cascade="all, delete-orphan",
        back_populates="person",
        passive_deletes=True,
    )

    user: Mapped["UserDB"] = relationship(
        "UserDB",
        back_populates="person",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="UserDB.person_id",
    )

    owner_user: Mapped["UserDB"] = relationship(
        "UserDB",
        foreign_keys=[owner_user_id],
    )
