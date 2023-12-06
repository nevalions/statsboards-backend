from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base
from . import SeasonRelationMixin

if TYPE_CHECKING:
    from .season import SeasonDB
    from .team import TeamDB


class TournamentDB(SeasonRelationMixin, Base):
    __tablename__ = "tournament"
    __table_args__ = {"extend_existing": True}
    _season_id_nullable = False
    _ondelete = "CASCADE"
    _season_back_populates = "tournaments"

    tournament_eesl_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        unique=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default="",
        server_default="",
    )
    tournament_logo_url: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )

    ## season_id: Mapped[int] = mapped_column(
    ##     ForeignKey("season.id", ondelete="CASCADE"), nullable=False
    ## )
    ## season: Mapped["SeasonDB"] = relationship(back_populates="tournaments")

    ### fk_season = Column(Integer, ForeignKey('season.year', ondelete="CASCADE"),
    ###                    nullable=False)

    ### seasons = relationship('SeasonDB',
    ###                        back_populates='tournaments')

    # matches = relationship('MatchDB', cascade="all, delete-orphan",
    #                        back_populates="tournaments", passive_deletes=True)
    teams = relationship(
        "TeamDB", secondary="team_tournament", back_populates="tournaments"
    )
    # lazy='subquery')
