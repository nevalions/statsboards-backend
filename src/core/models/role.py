from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .user_role import UserRoleDB


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

    users: Mapped[list["UserRoleDB"]] = relationship(
        "UserRoleDB",
        back_populates="role",
        cascade="all, delete-orphan",
    )
