import asyncio

from fastapi import HTTPException
from sqlalchemy import select, Result

from src.core.models import db, BaseServiceDB, SportDB
from .schemas import SportSchemaCreate, SportSchemaUpdate
from ..logging_config import get_logger, setup_logging

setup_logging()
ITEM = "SPORT"


class SportServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(
            database,
            model=SportDB,
        )
        self.logger = get_logger("backend_logger_SportServiceDB", self)
        self.logger.debug(f"Initialized SportServiceDB")

    async def create(self, item: SportSchemaCreate):
        self.logger.debug(f"Creat {ITEM}:{item}")
        try:
            season = self.model(
                title=item.title,
                description=item.description,
            )
            return await super().create(season)
        except Exception as e:
            self.logger.error(f"Error creating {ITEM} {e}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"Error creating {self.model.__name__}. Check input data. {ITEM}",
            )

    async def update(
        self,
        item_id: int,
        item: SportSchemaUpdate,
        **kwargs,
    ):
        self.logger.debug(f"Update {ITEM} with id:{item_id}")
        try:
            return await super().update(
                item_id,
                item,
                **kwargs,
            )
        except Exception as e:
            self.logger.error(f"Error updating {ITEM} {e}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"Error updating {self.model.__name__}. Check input data. {ITEM}",
            )

    async def get_tournaments_by_sport(
        self,
        sport_id: int,
        key: str = "id",
    ):
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
    ):
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
    ):
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
    ):
        self.logger.debug(f"Get positions by {ITEM} id:{sport_id}")
        return await self.get_related_item_level_one_by_key_and_value(
            key,
            sport_id,
            "positions",
        )
