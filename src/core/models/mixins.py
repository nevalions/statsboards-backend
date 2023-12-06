from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import declared_attr, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .season import SeasonDB
    from .tournament import TournamentDB


class SeasonRelationMixin:
    _season_id_nullable: bool = False
    _season_id_unique: bool = False
    _ondelete: str | None = None  # "CASCADE"
    _season_back_populates: str | None

    @declared_attr
    def season_id(cls) -> Mapped[int]:
        return mapped_column(
            ForeignKey("season.id", ondelete=cls._ondelete),
            unique=cls._season_id_unique,
            nullable=cls._season_id_nullable,
        )

    @declared_attr
    def season(cls) -> Mapped["SeasonDB"]:
        return relationship(
            "SeasonDB",
            back_populates=cls._season_back_populates,
        )
