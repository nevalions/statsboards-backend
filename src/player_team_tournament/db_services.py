from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions import NotFoundError
from src.core.models import BaseServiceDB, PlayerDB, PlayerTeamTournamentDB
from src.core.models.base import Database
from src.player.db_services import PlayerServiceDB

from ..logging_config import get_logger, setup_logging
from .schemas import (
    PlayerTeamTournamentSchemaCreate,
    PlayerTeamTournamentSchemaUpdate,
)

setup_logging()
ITEM = "PLAYER_TEAM_TOURNAMENT"


class PlayerTeamTournamentServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, PlayerTeamTournamentDB)
        self.logger = get_logger("backend_logger_PlayerTeamTournamentServiceDB")
        self.logger.debug("Initialized PlayerTeamTournamentServiceDB")

    async def create(
        self,
        item: PlayerTeamTournamentSchemaCreate | PlayerTeamTournamentSchemaUpdate,
    ) -> PlayerTeamTournamentDB:
        try:
            player_team_tournament = self.model(
                player_team_tournament_eesl_id=item.player_team_tournament_eesl_id,
                player_id=item.player_id,
                position_id=item.position_id,
                team_id=item.team_id,
                tournament_id=item.tournament_id,
                player_number=item.player_number,
            )
            self.logger.debug(
                f"Starting to create PlayerTeamTournamentDB with data: {player_team_tournament.__dict__}"
            )
            return await super().create(player_team_tournament)
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

    async def create_or_update_player_team_tournament(
        self,
        p: PlayerTeamTournamentSchemaCreate | PlayerTeamTournamentSchemaUpdate,
    ) -> PlayerTeamTournamentDB | None:
        try:
            self.logger.debug(f"Creat or update {ITEM}:{p}")
            if p.player_team_tournament_eesl_id:
                self.logger.debug(f"Get {ITEM} by eesl id")
                player_team_tournament_from_db = (
                    await self.get_player_team_tournament_by_eesl_id(
                        p.player_team_tournament_eesl_id
                    )
                )
                if player_team_tournament_from_db:
                    self.logger.debug(f"{ITEM} exist, updating...")
                    return await self.update_player_team_tournament_by_eesl(
                        "player_team_tournament_eesl_id",
                        PlayerTeamTournamentSchemaUpdate(**p.model_dump()),
                    )
                else:
                    self.logger.debug(f"{ITEM} does not exist, creating...")
                    return await self.create_new_player_team_tournament(
                        PlayerTeamTournamentSchemaCreate(**p.model_dump()),
                    )
            else:
                if p.tournament_id and p.player_id:
                    self.logger.debug(f"Got {ITEM} by player id and tournament id")
                    player_team_tournament_from_db = (
                        await self.get_player_team_tournaments_by_tournament_id(
                            p.tournament_id, p.player_id
                        )
                    )
                    if player_team_tournament_from_db:
                        self.logger.debug(f"{ITEM} exist, updating...")
                        return await self.update(player_team_tournament_from_db.id, PlayerTeamTournamentSchemaUpdate(**p.model_dump()))
                self.logger.debug(f"{ITEM} does not exist, creating...")
                return await self.create_new_player_team_tournament(
                    PlayerTeamTournamentSchemaCreate(**p.model_dump()),
                )
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Error creating or updating {ITEM}:{p} {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Database error creating or updating player team tournament",
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(
                f"Data error creating or updating {ITEM}:{p} {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided for player team tournament",
            )
        except NotFoundError as ex:
            self.logger.info(
                f"Not found creating or updating {ITEM}:{p} {ex}", exc_info=True
            )
            return None
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error creating or updating {ITEM}:{p} {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error creating or updating player team tournament",
            )

    async def update_player_team_tournament_by_eesl(
        self,
        eesl_field_name: str,
        p: PlayerTeamTournamentSchemaUpdate,
    ) -> PlayerTeamTournamentDB | None:
        try:
            self.logger.debug(f"Update {ITEM} by {eesl_field_name} {p}")
            if p.player_team_tournament_eesl_id is not None and isinstance(
                p.player_team_tournament_eesl_id, int
            ):
                return await self.update_item_by_eesl_id(
                    eesl_field_name,
                    p.player_team_tournament_eesl_id,
                    p,
                )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid player team tournament {eesl_field_name}",
            )
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Error updating {ITEM} by {eesl_field_name} {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Database error updating player team tournament",
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(
                f"Data error updating {ITEM} by {eesl_field_name} {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided for player team tournament",
            )
        except NotFoundError as ex:
            self.logger.info(
                f"Not found updating {ITEM} by {eesl_field_name} {ex}", exc_info=True
            )
            return None
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error updating {ITEM} by {eesl_field_name} {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error updating player team tournament",
            )

    async def create_new_player_team_tournament(
        self,
        p: PlayerTeamTournamentSchemaCreate,
    ) -> PlayerTeamTournamentDB:
        try:
            self.logger.debug(f"Create {ITEM} wit data {p}")
            player_team_tournament = self.model(
                player_team_tournament_eesl_id=p.player_team_tournament_eesl_id,
                player_id=p.player_id,
                position_id=p.position_id,
                team_id=p.team_id,
                tournament_id=p.tournament_id,
                player_number=p.player_number,
            )

            return await super().create(player_team_tournament)
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(f"Error creating {ITEM}{ex}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Database error creating player team tournament",
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(f"Data error creating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided for player team tournament",
            )
        except NotFoundError as ex:
            self.logger.info(f"Not found creating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(status_code=404, detail=str(ex))
        except Exception as ex:
            self.logger.critical(f"Unexpected error creating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Internal server error creating player team tournament",
            )

    async def get_player_team_tournament_by_eesl_id(
        self,
        value: int | str,
        field_name: str = "player_team_tournament_eesl_id",
    ) -> PlayerTeamTournamentDB | None:
        try:
            self.logger.debug(f"Get {ITEM} by {field_name}: {value}")
            return await self.get_item_by_field_value(
                value=value,
                field_name=field_name,
            )
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Error getting {ITEM} by {field_name}:{value} {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Database error fetching player team tournament",
            )

    async def get_player_team_tournaments_by_tournament_id(
        self, tournament_id: int, player_id: int
    ) -> PlayerTeamTournamentDB | None:
        try:
            self.logger.debug(
                f"Get {ITEM} by tournament id:{tournament_id} and player id:{player_id}"
            )
            async with self.db.async_session() as session:
                stmt = (
                    select(PlayerTeamTournamentDB)
                    .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
                    .where(PlayerTeamTournamentDB.player_id == player_id)
                )

                results = await session.execute(stmt)
                player = results.scalars().one_or_none()
                if player:
                    return player
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"{ITEM} does not exist",
                    )
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Error getting {ITEM} by tournament id:{tournament_id} and player id:{player_id} {ex}",
                exc_info=True,
            )
            return None
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(
                f"Data error getting {ITEM} by tournament id:{tournament_id} and player id:{player_id} {ex}",
                exc_info=True,
            )
            return None
        except NotFoundError as ex:
            self.logger.info(
                f"Not found {ITEM} by tournament id:{tournament_id} and player id:{player_id} {ex}",
                exc_info=True,
            )
            return None
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error getting {ITEM} by tournament id:{tournament_id} and player id:{player_id} {ex}",
                exc_info=True,
            )
            return None

    async def get_player_team_tournament_with_person(
        self, player_id: int
    ) -> PlayerDB | None:
        player_service = PlayerServiceDB(self.db)
        try:
            return await self.get_nested_related_item_by_id(
                player_id,
                player_service,
                "player",
                "person",
            )
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(f"Error getting {ITEM} with person {ex}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Database error fetching player team tournament with person",
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(f"Data error getting {ITEM} with person {ex}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided for player team tournament",
            )
        except NotFoundError as ex:
            self.logger.info(f"Not found {ITEM} with person {ex}", exc_info=True)
            return None
        except Exception as ex:
            self.logger.critical(f"Unexpected error getting {ITEM} with person {ex}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Internal server error fetching player team tournament with person",
            )

    async def update(
        self,
        item_id: int,
        item: PlayerTeamTournamentSchemaUpdate,
        **kwargs,
    ) -> PlayerTeamTournamentDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
