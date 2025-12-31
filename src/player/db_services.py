from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions import NotFoundError
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
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(f"Database error creating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Database error creating {self.model.__name__}",
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(f"Data error creating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided",
            )
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error in {self.__class__.__name__}.create: {ex}",
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
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
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Database error getting player {player_id} with person data: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Database error fetching player data",
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(
                f"Data error getting player {player_id} with person data: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided",
            )
        except NotFoundError as ex:
            self.logger.info(
                f"Player not found: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=404,
                detail=str(ex),
            )
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error in {self.__class__.__name__}.get_player_with_person({player_id}): {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
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
