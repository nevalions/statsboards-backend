# from typing import TYPE_CHECKING
#
# from sqlalchemy import Integer, ForeignKey
# from sqlalchemy.orm import Mapped, mapped_column, relationship
#
# from src.core.models import Base
#
# if TYPE_CHECKING:
#     from .team import TeamDB
#     from .match import MatchDB
#
#
# class FootballHomeTeamStartLineupDB(Base):
#     __tablename__ = "football_home_team_start_lineup"
#     __table_args__ = {"extend_existing": True}
#
#     match_id: Mapped[int] = mapped_column(
#         Integer,
#         ForeignKey(
#             "match.id",
#             ondelete="CASCADE",
#         ),
#         nullable=False,
#         unique=True,
#     )
#
#     home_team_id: Mapped[int] = mapped_column(
#         ForeignKey(
#             "match.team_a_id",
#             ondelete="CASCADE",
#         ),
#         nullable=False,
#     )
#
#     matches: Mapped["MatchDB"] = relationship(
#         "MatchDB",
#         back_populates="football_home_team_start_lineup",
#     )
