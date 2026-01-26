from typing import TYPE_CHECKING

from sqlalchemy import Integer, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models import Base

if TYPE_CHECKING:
    pass


class MatchStatsThrottleDB(Base):
    __tablename__ = "match_stats_throttle"
    __table_args__ = {"extend_existing": True}

    match_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    last_notified_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="NOW()"
    )
