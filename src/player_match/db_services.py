from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import BaseServiceDB, PlayerMatchDB
from src.positions.db_services import PositionServiceDB
from .schemas import PlayerMatchSchemaCreate, PlayerMatchSchemaUpdate
from ..logging_config import setup_logging, get_logger
from ..player.db_services import PlayerServiceDB
from ..player_team_tournament.db_services import PlayerTeamTournamentServiceDB


setup_logging()
ITEM = "PLAYER_MATCH"


class PlayerMatchServiceDB(BaseServiceDB):
    def __init__(
        self,
        database,
    ):
        super().__init__(database, PlayerMatchDB)
        self.logger = get_logger("backend_logger_PlayerMatchServiceDB")
        self.logger.debug(f"Initialized PlayerMatchServiceDB")

    async def create_or_update_player_match(
        self,
        p: PlayerMatchSchemaCreate | PlayerMatchSchemaUpdate,
    ):
        try:
            self.logger.debug(f"Creat or update {ITEM}:{p}")
            if p.player_match_eesl_id and p.match_id:
                self.logger.debug(f"Get {ITEM} by eesl id")
                player_match_from_db = (
                    await self.get_player_match_by_match_id_and_eesl_id(
                        p.match_id, p.player_match_eesl_id
                    )
                )
                if player_match_from_db and p.match_id == player_match_from_db.match_id:
                    if not player_match_from_db.is_start:
                        self.logger.debug(f"{ITEM} exist, updating...")
                        return await self.update_player_match_by_eesl(
                            p.match_id, p.player_match_eesl_id, p
                        )
                    else:
                        self.logger.warning(f"{ITEM} is in start, skipping...")
                        return player_match_from_db
                else:
                    self.logger.debug(f"{ITEM} does not exist, creating...")
                    return await self.create_new_player_match(
                        p,
                    )
            else:
                if p.match_id and p.player_team_tournament_id:
                    player_match_from_db = await self.get_players_match_by_match_id(
                        p.match_id, p.player_team_tournament_id
                    )
                    if (
                        player_match_from_db
                        and p.match_id == player_match_from_db.match_id
                    ):
                        self.logger.debug(f"{ITEM} already in match, updating...")
                        return await self.update_player_match(
                            player_match_from_db.id, p
                        )
                self.logger.debug(f"{ITEM} does not exist, creating...")
                return await self.create_new_player_match(
                    p,
                )
        except Exception as ex:
            self.logger.error(
                f"Error creating or updating {ITEM}:{p} {ex}", exc_info=True
            )

    async def create_new_player_match(
        self,
        p: PlayerMatchSchemaCreate,
    ):
        try:
            self.logger.debug(f"Create {ITEM} wit data {p}")
            player_match = self.model(
                player_match_eesl_id=p.player_match_eesl_id,
                player_team_tournament_id=p.player_team_tournament_id,
                match_position_id=p.match_position_id,
                match_id=p.match_id,
                match_number=p.match_number,
                team_id=p.team_id,
                is_start=p.is_start,
            )
            return await super().create(player_match)
        except Exception as ex:
            self.logger.error(f"Error creating {ITEM}{ex}", exc_info=True)

    async def get_player_match_by_match_id_and_eesl_id(
        self, match_id, player_match_eesl_id
    ):
        try:
            self.logger.debug(
                f"Get {ITEM} by match id:{match_id} and eesl id:{player_match_eesl_id}"
            )
            async with self.db.async_session() as session:
                stmt = (
                    select(PlayerMatchDB)
                    .where(PlayerMatchDB.match_id == match_id)
                    .where(PlayerMatchDB.player_match_eesl_id == player_match_eesl_id)
                )

                result = await session.execute(stmt)
                player = result.scalars().one_or_none()
                if player:
                    self.logger.debug(f"{ITEM} found {player}")
                    return player
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"{ITEM} not found",
                    )
        except Exception as ex:
            self.logger.error(
                f"Error getting {ITEM} by match id{match_id} and eesl id:{player_match_eesl_id} {ex}",
                exc_info=True,
            )

    async def update_player_match_by_eesl(self, match_id, eesl_id, new_player):
        try:
            player = await self.get_player_match_by_match_id_and_eesl_id(
                match_id, eesl_id
            )
            if player:
                updated_player = await self.update_player_match(player.id, new_player)
                if updated_player:
                    return updated_player
            raise HTTPException(status_code=404, detail=f"{ITEM} not found to update")
        except Exception as ex:
            self.logger.error(
                f"Error updating {ITEM}{ex} by match eesl{eesl_id}", exc_info=True
            )

    async def get_players_match_by_match_id(self, match_id, player_team_tournament_id):
        async with self.db.async_session() as session:
            try:
                self.logger.debug(f"Get {ITEM} by match id:{match_id}")
                stmt = (
                    select(PlayerMatchDB)
                    .where(PlayerMatchDB.match_id == match_id)
                    .where(
                        PlayerMatchDB.player_team_tournament_id
                        == player_team_tournament_id
                    )
                )

                results = await session.execute(stmt)
                players = results.scalars().one_or_none()
                return players
            except Exception as ex:
                self.logger.error(
                    f"Error getting {ITEM} by match id:{match_id} {ex}", exc_info=True
                )

    async def get_player_in_sport(self, player_id: int):
        player_service = PlayerTeamTournamentServiceDB(self.db)
        try:
            self.logger.debug(f"Get player in sport by player_id:{player_id}")
            return await self.get_nested_related_item_by_id(
                player_id,
                player_service,
                "player_team_tournament",
                "player",
            )
        except Exception as ex:
            self.logger.error(f"Error getting player in sport {ex}", exc_info=True)

    async def get_player_person_in_match(self, player_id: int):
        player_service = PlayerServiceDB(self.db)
        try:
            self.logger.debug(
                f"Get {ITEM} in sport with person by player_id:{player_id}"
            )
            p = await self.get_player_in_sport(player_id)
            if p:
                return await player_service.get_player_with_person(p.id)
        except Exception as ex:
            self.logger.error(
                f"Error getting {ITEM} in sport with person {ex}", exc_info=True
            )

    async def get_player_in_team_tournament(
        self,
        match_id: int,
    ):
        try:
            self.logger.debug(f"Get player_team_tournament by match_id:{match_id}")
            return await self.get_related_item_level_one_by_id(
                match_id,
                "player_team_tournament",
            )
        except Exception as ex:
            self.logger.error(
                f"Error getting player_team_tournament {ex}", exc_info=True
            )

    async def get_player_in_match_full_data(self, match_player_id: int):
        try:
            self.logger.debug(f"Get {ITEM} in match with full data")
            match_player = await self.get_by_id(match_player_id)
            team_tournament_player = await self.get_player_in_team_tournament(
                match_player_id
            )
            person = await self.get_player_person_in_match(match_player_id)
            position = await PositionServiceDB(self.db).get_by_id(
                match_player.match_position_id
            )

            return {
                "match_player": match_player,
                "player_team_tournament": team_tournament_player,
                "person": person,
                "position": position,
            }
        except Exception as ex:
            self.logger.error(
                f"Error getting {ITEM} with full data {ex}", exc_info=True
            )

    async def update(
        self,
        item_id: int,
        item: PlayerMatchSchemaUpdate,
        **kwargs,
    ):
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
