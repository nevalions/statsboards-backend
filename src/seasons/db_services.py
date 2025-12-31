from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions import NotFoundError

from src.core.models import (
    BaseServiceDB,
    MatchDB,
    SeasonDB,
    SportDB,
    TeamDB,
    TournamentDB,
)
from src.core.models.base import Database
from src.logging_config import get_logger

from .schemas import SeasonSchemaCreate, SeasonSchemaUpdate
ITEM = "SEASON"


class SeasonServiceDB(BaseServiceDB):
    def __init__(self, database: Database) -> None:
        super().__init__(
            database,
            model=SeasonDB,
        )
        self.logger = get_logger("backend_logger_SeasonServiceDB", self)
        self.logger.debug("Initialized SeasonServiceDB")

    async def create(self, item: SeasonSchemaCreate) -> SeasonDB:
        self.logger.debug(f"Creat {ITEM}:{item}")
        try:
            season = self.model(
                year=item.year,
                description=item.description,
            )
            return await super().create(season)
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(f"Error creating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"Error creating {self.model.__name__}. Check input data. {ITEM}",
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(f"Data error creating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data provided for {ITEM}",
            )
        except NotFoundError as ex:
            self.logger.info(f"Not found creating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(status_code=404, detail=str(ex))
        except Exception as ex:
            self.logger.critical(f"Unexpected error creating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

    async def update(
        self,
        item_id: int,
        item: SeasonSchemaUpdate,
        **kwargs,
    ) -> SeasonDB | None:
        self.logger.debug(f"Update {ITEM} with id:{item_id}")
        if item.year is None:
            raise HTTPException(
                status_code=409,
                detail=f"Error updating {self.model.__name__}. Check input data. {ITEM}",
            )
        try:
            return await super().update(
                item_id,
                item,
                **kwargs,
            )
        except HTTPException as e:
            if e.status_code == 404:
                return None
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(f"Error updating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"Error updating {self.model.__name__}. Check input data. {ITEM}",
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(f"Data error updating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data provided for {ITEM}",
            )
        except NotFoundError as ex:
            self.logger.info(f"Not found updating {ITEM}: {ex}", exc_info=True)
            return None
        except Exception as ex:
            self.logger.critical(f"Unexpected error updating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_season_by_year(self, season_year: int) -> SeasonDB | None:
        async with self.db.async_session() as session:
            self.logger.debug(f"Get {ITEM}s by year id:{season_year}")
            season = await session.execute(select(SeasonDB).filter_by(year=season_year))
            return season.scalars().one_or_none()

    async def get_tournaments_by_year(
        self,
        year: int,
        key: str = "year",
    ) -> list[TournamentDB]:
        self.logger.debug(f"Get tournaments by {ITEM} year:{year}")
        try:
            tournaments = await self.get_related_item_level_one_by_key_and_value(
                key,
                year,
                "tournaments",
            )
            if not tournaments:
                return []
            return tournaments
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(f"Error getting tournaments: {ex}", exc_info=True)
            return []
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(f"Data error getting tournaments: {ex}", exc_info=True)
            return []
        except NotFoundError as ex:
            self.logger.info(f"Not found getting tournaments: {ex}", exc_info=True)
            return []
        except Exception as ex:
            self.logger.critical(f"Unexpected error getting tournaments: {ex}", exc_info=True)
            return []

    async def get_tournaments_by_year_and_sport(
        self,
        year: int,
        sport_id: int,
    ) -> list[TournamentDB]:
        async with self.db.async_session() as session:
            self.logger.debug(f"Get tournaments by {ITEM} year:{year} id:{sport_id}")
            stmt = (
                select(TournamentDB)
                .join(SeasonDB, TournamentDB.season_id == SeasonDB.id)
                .join(SportDB, TournamentDB.sport_id == SportDB.id)
                .where(and_(SeasonDB.year == year, SportDB.id == sport_id))
            )
            try:
                results = await session.execute(stmt)
                tournaments = results.scalars().all()
                self.logger.info(f"Got tournaments: {tournaments}")
                return tournaments
            except HTTPException:
                raise
            except (IntegrityError, SQLAlchemyError) as ex:
                self.logger.error(f"Error getting tournaments: {ex}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Database error getting tournaments",
                )
            except (ValueError, KeyError, TypeError) as ex:
                self.logger.warning(f"Data error getting tournaments: {ex}", exc_info=True)
                raise HTTPException(
                    status_code=400,
                    detail="Invalid data provided for tournaments",
                )
            except NotFoundError as ex:
                self.logger.info(f"Not found getting tournaments: {ex}", exc_info=True)
                return []
            except Exception as ex:
                self.logger.critical(f"Unexpected error getting tournaments: {ex}", exc_info=True)
                raise HTTPException(status_code=500, detail="Internal server error")

    async def get_tournaments_by_season_and_sport_ids(
        self,
        season_id: int,
        sport_id: int,
    ) -> list[TournamentDB]:
        self.logger.debug(
            f"Get tournaments by {ITEM} id:{season_id} and sport_id:{sport_id}"
        )
        async with self.db.async_session() as session:
            stmt = (
                select(TournamentDB)
                .join(SeasonDB, TournamentDB.season_id == SeasonDB.id)
                .join(SportDB, TournamentDB.sport_id == SportDB.id)
                .where(and_(SeasonDB.id == season_id, SportDB.id == sport_id))
            )
            try:
                results = await session.execute(stmt)
                tournaments = results.scalars().all()
                self.logger.debug(f"Got number of tournaments: {len(tournaments)}")
                return tournaments
            except HTTPException:
                raise
            except (IntegrityError, SQLAlchemyError) as ex:
                self.logger.error(f"Error getting tournaments: {ex}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Database error getting tournaments",
                )
            except (ValueError, KeyError, TypeError) as ex:
                self.logger.warning(f"Data error getting tournaments: {ex}", exc_info=True)
                raise HTTPException(
                    status_code=400,
                    detail="Invalid data provided for tournaments",
                )
            except NotFoundError as ex:
                self.logger.info(f"Not found getting tournaments: {ex}", exc_info=True)
                return []
            except Exception as ex:
                self.logger.critical(f"Unexpected error getting tournaments: {ex}", exc_info=True)
                raise HTTPException(status_code=500, detail="Internal server error")

    async def get_teams_by_year(
        self,
        year: int,
        key: str = "year",
    ) -> list[TeamDB]:
        self.logger.debug(f"Get teams by {ITEM} year:{year}")
        return await self.get_related_items_by_two(
            filter_key=key,
            filter_value=year,
            second_model=TournamentDB,
            related_property="tournaments",
            second_level_property="teams",
        )

    async def get_matches_by_year(
        self,
        year: int,
        key: str = "year",
    ) -> list[MatchDB]:
        self.logger.debug(f"Get teams by {ITEM} year:{year}")
        return await self.get_related_items_by_two(
            filter_key=key,
            filter_value=year,
            second_model=TournamentDB,
            related_property="tournaments",
            second_level_property="matches",
        )
