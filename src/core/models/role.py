from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from src.core.models.user import UserDB


class RoleDB(Base):
    __tablename__ = "role"
    __table_args__ = {"extend_existing": True}

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )

    users: Mapped[list["UserDB"]] = relationship(
        "UserDB",
        secondary="user_role",
        back_populates="roles",
    )
