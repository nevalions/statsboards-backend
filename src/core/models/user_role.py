from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from src.core.models import Base

if TYPE_CHECKING:
    pass


class UserRoleDB(Base):
    __tablename__ = "user_role"
    __table_args__ = {"extend_existing": True}

    @declared_attr
    def id(self) -> None:
        return None

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("role.id", ondelete="CASCADE"),
        primary_key=True,
    )
