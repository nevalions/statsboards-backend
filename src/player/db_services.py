from typing import TYPE_CHECKING

from src.core.decorators import handle_service_exceptions
from src.core.models import BaseServiceDB, PlayerDB
from src.core.models.base import Database

from ..logging_config import get_logger
from .schemas import PlayerSchema, PlayerSchemaCreate, PlayerSchemaUpdate

if TYPE_CHECKING:
    from src.core.models import PlayerDB
ITEM = "PLAYER"


class PlayerServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, PlayerDB)
        self.logger = get_logger("backend_logger_PlayerServiceDB", self)
        self.logger.debug("Initialized PlayerServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(
        self,
        item: PlayerSchemaCreate | PlayerSchemaUpdate,
    ) -> PlayerDB:
        player = self.model(
            player_eesl_id=item.player_eesl_id,
            sport_id=item.sport_id,
            person_id=item.person_id,
        )
        self.logger.debug(f"Starting to create PlayerDB with data: {player.__dict__}")
        return await super().create(player)

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

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching with person", reraise_not_found=True
    )
    async def get_player_with_person(self, player_id: int) -> PlayerSchema:
        self.logger.debug(f"Get {ITEM} with person data {player_id}")
        player_with_person_data = await self.get_related_item_level_one_by_id(player_id, "person")
        if player_with_person_data:
            self.logger.debug(f"Got {ITEM} with person data {player_with_person_data}")
            return player_with_person_data
        else:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404,
                detail=f"Person does not exist for {ITEM} id:{player_id}",
            )

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
