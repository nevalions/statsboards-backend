from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions import NotFoundError
from src.core.models import (
    BaseServiceDB,
    PlayerDB,
    PositionDB,
    SportDB,
    TeamDB,
    TournamentDB,
)
from src.core.models.base import Database

from ..logging_config import get_logger
from .schemas import SportSchemaCreate, SportSchemaUpdate

ITEM = "SPORT"


class SportServiceDB(BaseServiceDB):
    def __init__(self, database: Database) -> None:
        super().__init__(
            database,
            model=SportDB,
        )
        self.logger = get_logger("backend_logger_SportServiceDB", self)
        self.logger.debug("Initialized SportServiceDB")

    async def create(self, item: SportSchemaCreate) -> SportDB:
        self.logger.debug(f"Creat {ITEM}:{item}")
        try:
            season = self.model(
                title=item.title,
                description=item.description,
            )
            return await super().create(season)
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as e:
            self.logger.error(f"Database error creating {ITEM}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Database error creating {self.model.__name__}",
            )
        except (ValueError, KeyError, TypeError) as e:
            self.logger.warning(f"Data error creating {ITEM}: {e}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided",
            )
        except Exception as e:
            self.logger.critical(
                f"Unexpected error in {self.__class__.__name__}.create: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
            )

    async def update(
        self,
        item_id: int,
        item: SportSchemaUpdate,
        **kwargs,
    ) -> SportDB:
        self.logger.debug(f"Update {ITEM} with id:{item_id}")
        try:
            return await super().update(
                item_id,
                item,
                **kwargs,
            )
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as e:
            self.logger.error(f"Database error updating {ITEM}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Database error updating {self.model.__name__}",
            )
        except (ValueError, KeyError, TypeError) as e:
            self.logger.warning(f"Data error updating {ITEM}: {e}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided",
            )
        except NotFoundError as e:
            self.logger.info(f"Not found: {e}", exc_info=True)
            raise HTTPException(
                status_code=404,
                detail="Resource not found",
            )
        except Exception as e:
            self.logger.critical(
                f"Unexpected error in {self.__class__.__name__}.update({item_id}): {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
            )

    async def get_tournaments_by_sport(
        self,
        sport_id: int,
        key: str = "id",
    ) -> list[TournamentDB]:
        self.logger.debug(f"Get tournaments by {ITEM} id:{sport_id}")
        return await self.get_related_item_level_one_by_key_and_value(
            key,
            sport_id,
            "tournaments",
        )

    async def get_teams_by_sport(
        self,
        sport_id: int,
        key: str = "id",
    ) -> list[TeamDB]:
        self.logger.debug(f"Get teams by {ITEM} id:{sport_id}")
        return await self.get_related_item_level_one_by_key_and_value(
            key,
            sport_id,
            "teams",
        )

    async def get_players_by_sport(
        self,
        sport_id: int,
        key: str = "id",
    ) -> list[PlayerDB]:
        self.logger.debug(f"Get players by {ITEM} id:{sport_id}")
        return await self.get_related_item_level_one_by_key_and_value(
            key,
            sport_id,
            "players",
        )

    async def get_positions_by_sport(
        self,
        sport_id: int,
        key: str = "id",
    ) -> list[PositionDB]:
        self.logger.debug(f"Get positions by {ITEM} id:{sport_id}")
        return await self.get_related_item_level_one_by_key_and_value(
            key,
            sport_id,
            "positions",
        )
