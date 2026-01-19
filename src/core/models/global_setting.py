from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models import Base


class GlobalSettingDB(Base):
    __tablename__ = "global_setting"
    __table_args__ = {"extend_existing": True}

    key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default="",
    )
    value_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="string",
        server_default="string",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
