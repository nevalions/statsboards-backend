from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import BaseServiceDB, MatchDB, PlayerMatchDB, TeamDB
from src.logging_config import get_logger, setup_logging
from src.player_match.db_services import PlayerMatchServiceDB
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB

from .shemas import MatchSchemaCreate, MatchSchemaUpdate

setup_logging()
ITEM = "MATCH"


class MatchServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, MatchDB)
        self.logger = get_logger("backend_logger_MatchServiceDB", self)
        self.logger.debug("Initialized MatchServiceDB")

    async def create_or_update_match(self, m: MatchSchemaCreate):
        try:
            self.logger.debug(f"Creat or update {ITEM}:{m}")
            if m.match_eesl_id:
                self.logger.debug(f"Get {ITEM} eesl_id:{m.match_eesl_id}")
                match_from_db = await self.get_match_by_eesl_id(m.match_eesl_id)
                if match_from_db:
                    self.logger.debug(
                        f"{ITEM} eesl_id:{m.match_eesl_id} already exists updating"
                    )
                    return await self.update_match_by_eesl(
                        "match_eesl_id",
                        m,
                    )
                else:
                    return await self.create_new_match(m)
            else:
                return await self.create_new_match(m)
        except Exception as ex:
            self.logger.error(f"{ITEM} {m} returned an error: {ex}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"{ITEM} ({m}) returned some error",
            )

    async def update_match_by_eesl(
        self,
        eesl_field_name: str,
        m: MatchSchemaCreate,
    ):
        self.logger.debug(f"Update {ITEM} {eesl_field_name}:{m.match_eesl_id}")
        return await self.update_item_by_eesl_id(
            eesl_field_name,
            m.match_eesl_id,
            m,
        )

    async def create_new_match(self, m: MatchSchemaCreate):
        match = MatchDB(
            match_date=m.match_date,
            week=m.week,
            match_eesl_id=m.match_eesl_id,
            team_a_id=m.team_a_id,
            team_b_id=m.team_b_id,
            tournament_id=m.tournament_id,
            sponsor_line_id=m.sponsor_line_id,
            main_sponsor_id=m.main_sponsor_id,
        )
        self.logger.debug(f"Create new {ITEM}:{match}")
        return await super().create(match)

    async def get_match_by_eesl_id(
        self,
        value,
        field_name="match_eesl_id",
    ):
        self.logger.debug(f"Get {ITEM} {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def update_match(
        self,
        item_id: int,
        item: MatchSchemaUpdate,
        **kwargs,
    ):
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    async def get_sport_by_match_id(self, match_id: int):
        self.logger.debug(f"Get sport by {ITEM} id:{match_id}")
        tournament_service = TournamentServiceDB(self.db)
        sport_service = SportServiceDB(self.db)
        match = await self.get_by_id(match_id)
        try:
            if match:
                tournament = await tournament_service.get_by_id(match.tournament_id)
                if tournament:
                    return await sport_service.get_by_id(tournament.sport_id)
        except Exception as ex:
            self.logger.error(
                f"No Sport found for match_id:{match_id} {ex}", exc_info=True
            )

    async def get_teams_by_match_id(
        self,
        match_id: int,
    ):
        self.logger.debug(f"Get teams by {ITEM} id:{match_id}")
        try:
            async with self.db.async_session() as session:
                team_service = TeamServiceDB(self.db)
                match = await self.get_by_id(match_id)
                if match:
                    home_team = await team_service.get_by_id(match.team_a_id)
                    away_team = await team_service.get_by_id(match.team_b_id)
                    return {
                        "home_team": home_team,
                        "away_team": away_team,
                    }
        except Exception as ex:
            self.logger.error(
                f"Error not all teams found for match_id:{match_id} {ex}", exc_info=True
            )

    async def get_match_sponsor_line(self, match_id: int):
        self.logger.debug(f"Get sponsor_line by {ITEM} id:{match_id}")
        return await self.get_related_item_level_one_by_id(match_id, "sponsor_line")

    async def get_matchdata_by_match(
        self,
        match_id: int,
    ):
        self.logger.debug(f"Get match_data by {ITEM} id:{match_id}")
        return await self.get_related_item_level_one_by_id(
            match_id,
            "match_data",
        )

    async def get_playclock_by_match(
        self,
        match_id: int,
    ):
        self.logger.debug(f"Get match_playclock by {ITEM} id:{match_id}")
        return await self.get_related_item_level_one_by_id(
            match_id,
            "match_playclock",
        )

    async def get_gameclock_by_match(
        self,
        match_id: int,
    ):
        self.logger.debug(f"Get match_gameclock by {ITEM} id:{match_id}")
        return await self.get_related_item_level_one_by_id(
            match_id,
            "match_gameclock",
        )

    async def get_teams_by_match(
        self,
        match_id: int,
    ):
        self.logger.debug(f"Get teams v2 by {ITEM} id:{match_id}")
        match = await self.get_related_items(
            match_id,
        )
        if match:
            try:
                team_a = await self.get_by_id_and_model(
                    model=TeamDB,
                    item_id=match.team_a_id,
                )
                team_b = await self.get_by_id_and_model(
                    model=TeamDB,
                    item_id=match.team_b_id,
                )

                return {
                    "team_a": team_a.__dict__,
                    "team_b": team_b.__dict__,
                }
            except Exception as ex:
                self.logger.error(
                    f"Error not all teams found for match_id:{match_id} {ex}",
                    exc_info=True,
                )
        return None

    async def get_players_by_match(
        self,
        match_id: int,
    ):
        self.logger.debug(f"Get players by {ITEM} id:{match_id}")
        try:
            async with self.db.async_session() as session:
                stmt = select(PlayerMatchDB).where(PlayerMatchDB.match_id == match_id)

                results = await session.execute(stmt)
                players = results.scalars().all()
                return players
        except Exception as ex:
            self.logger.error(
                f"Error getting players for {ITEM} id:{match_id} {ex}", exc_info=True
            )

    async def get_player_by_match_full_data(self, match_id: int):
        self.logger.debug(f"Get players with full data by {ITEM} id:{match_id}")
        player_service = PlayerMatchServiceDB(self.db)
        players = await self.get_players_by_match(match_id)
        players_with_data = []
        try:
            if players:
                for player in players:
                    p = await player_service.get_player_in_match_full_data(player.id)
                    players_with_data.append(p)
                return players_with_data
        except Exception as ex:
            self.logger.error(
                f"Error getting players with full data for {ITEM} id:{match_id} {ex}",
                exc_info=True,
            )
        return players_with_data

    async def get_scoreboard_by_match(
        self,
        match_id: int,
    ):
        self.logger.debug(f"Getting scoreboard for {ITEM} id:{match_id}")
        try:
            result = await self.get_related_item_level_one_by_id(
                match_id,
                "match_scoreboard",
            )
            self.logger.debug(f"Got scoreboard successfully. Result: {result}")
            return result
        except Exception as e:
            self.logger.error(
                f"Error getting scoreboard for {ITEM} id:{match_id} {e}", exc_info=True
            )
            raise

    # async def get_scoreboard_by_match(
    #     self,
    #     match_id: int,
    # ):
    #     return await self.get_related_item_level_one_by_id(
    #         match_id,
    #         "match_scoreboard",
    #     )


# async def get_match_db() -> MatchServiceDB:
#     yield MatchServiceDB(db)
#
#
# async def async_main() -> None:
#     match_service = MatchServiceDB(db)
#     # t = await team_service.get_team_by_id(1)
#     # t = await team_service.find_team_tournament_relation(6, 2)
#     # print(t)
#     # t = await team_service.get_team_by_eesl_id(1)
#     # u = await match_service.create_match()
#     # if t:
#     #     print(t.__dict__)
#
#
# if __name__ == "__main__":
#     asyncio.run(async_main())
