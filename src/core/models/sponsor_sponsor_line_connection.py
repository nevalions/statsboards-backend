from sqlalchemy import (
    Integer,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from src.core.models import Base


class SponsorSponsorLineDB(Base):
    __tablename__ = "sponsor_sponsor_line"
    __table_args__ = (
        UniqueConstraint(
            "sponsor_line_id",
            "sponsor_id",
            name="idx_unique_sponsor_sponsor_line",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sponsor_line_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "sponsor_line.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    sponsor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "sponsor.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
