from typing import TYPE_CHECKING

from fastapi import HTTPException

from src.core.models import BaseServiceDB, PlayerDB
from src.core.models.base import Database

from ..logging_config import get_logger, setup_logging
from .schemas import PlayerSchema, PlayerSchemaCreate, PlayerSchemaUpdate

if TYPE_CHECKING:
    from src.core.models import PlayerDB

setup_logging()
ITEM = "PLAYER"


class PlayerServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, PlayerDB)
        self.logger = get_logger("backend_logger_PlayerServiceDB", self)
        self.logger.debug("Initialized PlayerServiceDB")

    async def create(
        self,
        item: PlayerSchemaCreate | PlayerSchemaUpdate,
    ) -> PlayerDB:
        try:
            player = self.model(
                player_eesl_id=item.player_eesl_id,
                sport_id=item.sport_id,
                person_id=item.person_id,
            )
            self.logger.debug(
                f"Starting to create PlayerDB with data: {player.__dict__}"
            )
            return await super().create(player)
        except Exception as ex:
            self.logger.error(f"Error creating {ITEM} {ex}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"Error creating {self.model.__name__}. Check input data. {ITEM}",
            )

    async def create_or_update_player(
        self,
        p: PlayerSchemaCreate | PlayerSchemaUpdate,
    ) -> PlayerDB | None:
        return await super().create_or_update(p, eesl_field_name="player_eesl_id")

    async def get_player_by_eesl_id(
        self,
        value: int | str,
        field_name: str = "player_eesl_id",
    ) -> PlayerDB | None:
        self.logger.debug(f"Get {ITEM} {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def get_player_with_person(self, player_id: int) -> PlayerSchema:
        self.logger.debug(f"Get {ITEM} with person data {player_id}")
        try:
            player_with_person_data = await self.get_related_item_level_one_by_id(
                player_id, "person"
            )
            if player_with_person_data:
                self.logger.debug(
                    f"Got {ITEM} with person data {player_with_person_data}"
                )
                return player_with_person_data
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Person does not exist for {ITEM} id:{player_id}",
                )
        except Exception as ex:
            self.logger.error(
                f"{ITEM} with id:{player_id} returned an error while getting person data: {ex}",
                exc_info=True,
            )
            raise

    async def update(
        self,
        item_id: int,
        item: PlayerSchemaUpdate,
        **kwargs,
    ) -> PlayerDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
