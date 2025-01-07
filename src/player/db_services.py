from fastapi import HTTPException

from src.core.models import BaseServiceDB, PlayerDB
from .schemas import PlayerSchemaCreate, PlayerSchemaUpdate, PlayerSchema
from ..logging_config import get_logger, setup_logging

setup_logging()
ITEM = "PLAYER"


class PlayerServiceDB(BaseServiceDB):
    def __init__(
        self,
        database,
    ):
        super().__init__(database, PlayerDB)
        self.logger = get_logger("backend_logger_PlayerServiceDB", self)
        self.logger.debug(f"Initialized PlayerServiceDB")

    async def create_or_update_player(
        self,
        p: PlayerSchemaCreate | PlayerSchemaUpdate,
    ):
        try:
            self.logger.debug(f"Creat or update {ITEM}:{p}")
            if p.player_eesl_id:
                player_from_db = await self.get_player_by_eesl_id(p.player_eesl_id)
                if player_from_db:
                    self.logger.debug(
                        f"{ITEM} eesl_id:{p.player_eesl_id} already exists updating"
                    )
                    self.logger.debug(f"Get {ITEM} eesl_id:{p.player_eesl_id}")
                    return await self.update_player_by_eesl(
                        "player_eesl_id",
                        p,
                    )
                else:
                    return await self.create_new_player(
                        p,
                    )
            else:
                return await self.create_new_player(
                    p,
                )
        except Exception as ex:
            self.logger.error(f"{ITEM} {p} returned an error: {ex}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"{ITEM} ({p}) returned some error",
            )

    async def update_player_by_eesl(
        self,
        eesl_field_name: str,
        p: PlayerSchemaUpdate,
    ):
        self.logger.debug(f"Update {ITEM} {eesl_field_name}:{p.player_eesl_id}")
        return await self.update_item_by_eesl_id(
            eesl_field_name,
            p.player_eesl_id,
            p,
        )

    async def create_new_player(
        self,
        p: PlayerSchemaCreate,
    ):
        player = self.model(
            sport_id=p.sport_id,
            person_id=p.person_id,
            player_eesl_id=p.player_eesl_id,
        )
        self.logger.debug(f"Create new {ITEM}:{p}")
        return await super().create(player)

    async def get_player_by_eesl_id(
        self,
        value,
        field_name="player_eesl_id",
    ):
        self.logger.debug(f"Get {ITEM} {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def get_player_with_person(self, player_id) -> PlayerSchema:
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

    async def update_player(
        self,
        item_id: int,
        item: PlayerSchemaUpdate,
        **kwargs,
    ):
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
