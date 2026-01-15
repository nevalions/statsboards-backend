from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .match import MatchDB
    from .person import PersonDB
    from .player import PlayerDB
    from .role import RoleDB
    from .team import TeamDB
    from .tournament import TournamentDB


class UserDB(Base):
    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}

    person_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("person.id", ondelete="CASCADE"),
        nullable=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    person: Mapped["PersonDB"] = relationship(
        "PersonDB",
        back_populates="user",
        foreign_keys="UserDB.person_id",
    )

    tournaments: Mapped[list["TournamentDB"]] = relationship(
        "TournamentDB",
        back_populates="user",
    )

    players: Mapped[list["PlayerDB"]] = relationship(
        "PlayerDB",
        back_populates="user",
    )

    matches: Mapped[list["MatchDB"]] = relationship(
        "MatchDB",
        back_populates="user",
    )

    teams: Mapped[list["TeamDB"]] = relationship(
        "TeamDB",
        back_populates="user",
    )

    roles: Mapped[list["RoleDB"]] = relationship(
        "RoleDB",
        secondary="user_role",
        back_populates="users",
    )
