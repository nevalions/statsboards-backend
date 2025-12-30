from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import selectinload

from src.core.models import (
    BaseServiceDB,
    GameClockDB,
    MatchDataDB,
    MatchDB,
    PlayClockDB,
    PlayerMatchDB,
    ScoreboardDB,
    SponsorLineDB,
    SportDB,
    TeamDB,
)
from src.core.models.base import Database
from src.logging_config import get_logger, setup_logging
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB

from .schemas import MatchSchemaCreate, MatchSchemaUpdate

setup_logging()
ITEM = "MATCH"


class MatchServiceDB(BaseServiceDB):
    def __init__(self, database: Database) -> None:
        super().__init__(database, MatchDB)
        self.logger = get_logger("backend_logger_MatchServiceDB", self)
        self.logger.debug("Initialized MatchServiceDB")

    async def create(
        self,
        item: MatchSchemaCreate | MatchSchemaUpdate,
    ) -> MatchDB:
        try:
            match = self.model(
                match_date=item.match_date,
                week=item.week,
                match_eesl_id=item.match_eesl_id,
                team_a_id=item.team_a_id,
                team_b_id=item.team_b_id,
                tournament_id=item.tournament_id,
                sponsor_line_id=item.sponsor_line_id,
                main_sponsor_id=item.main_sponsor_id,
            )
            self.logger.debug(f"Starting to create MatchDB with data: {match.__dict__}")
            return await super().create(match)
        except Exception as ex:
            self.logger.error(f"Error creating {ITEM} {ex}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"Error creating {self.model.__name__}. Check input data. {ITEM}",
            )

    async def create_or_update_match(self, m: MatchSchemaCreate) -> MatchDB:
        return await super().create_or_update(m, eesl_field_name="match_eesl_id")

    async def get_match_by_eesl_id(
        self,
        value: int | str,
        field_name: str = "match_eesl_id",
    ) -> MatchDB | None:
        self.logger.debug(f"Get {ITEM} {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def update(
        self,
        item_id: int,
        item: MatchSchemaUpdate,
        **kwargs,
    ) -> MatchDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    async def get_sport_by_match_id(self, match_id: int) -> SportDB | None:
        self.logger.debug(f"Get sport by {ITEM} id:{match_id}")
        tournament_service = TournamentServiceDB(self.db)
        sport_service = SportServiceDB(self.db)
        match = await self.get_by_id(match_id)
        try:
            if match:
                tournament = await tournament_service.get_by_id(match.tournament_id)
                if tournament:
                    return await sport_service.get_by_id(tournament.sport_id)
            return None
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Database error fetching sport for match_id:{match_id} {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error fetching sport for match {match_id}",
            )
        except Exception as ex:
            self.logger.error(
                f"No Sport found for match_id:{match_id} {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error fetching sport for match {match_id}",
            )

    async def get_teams_by_match_id(
        self,
        match_id: int,
    ) -> dict | None:
        self.logger.debug(f"Get teams by {ITEM} id:{match_id}")
        try:
            async with self.db.async_session():
                team_service = TeamServiceDB(self.db)
                match = await self.get_by_id(match_id)
                if match:
                    home_team = await team_service.get_by_id(match.team_a_id)
                    away_team = await team_service.get_by_id(match.team_b_id)
                    return {
                        "home_team": home_team,
                        "away_team": away_team,
                    }
                return None
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Database error fetching teams for match_id:{match_id} {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error fetching teams for match {match_id}",
            )
        except Exception as ex:
            self.logger.error(
                f"Error not all teams found for match_id:{match_id} {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error fetching teams for match {match_id}",
            )

    async def get_match_sponsor_line(self, match_id: int) -> SponsorLineDB | None:
        self.logger.debug(f"Get sponsor_line by {ITEM} id:{match_id}")
        result = await self.get_related_item_level_one_by_id(match_id, "sponsor_line")
        if result:
            if hasattr(result, "__len__"):
                if len(result) > 0:
                    return result[0]  # type: ignore[return-value]
                return None
            return result  # type: ignore[return-value]
        return None

    async def get_matchdata_by_match(
        self,
        match_id: int,
    ) -> MatchDataDB | None:
        self.logger.debug(f"Get match_data by {ITEM} id:{match_id}")
        result = await self.get_related_item_level_one_by_id(
            match_id,
            "match_data",
        )
        if result:
            if hasattr(result, "__len__"):
                if len(result) > 0:
                    return result[0]  # type: ignore[return-value]
                return None
            return result  # type: ignore[return-value]
        return None

    async def get_playclock_by_match(
        self,
        match_id: int,
    ) -> PlayClockDB | None:
        self.logger.debug(f"Get match_playclock by {ITEM} id:{match_id}")
        result = await self.get_related_item_level_one_by_id(
            match_id,
            "match_playclock",
        )
        if result:
            if hasattr(result, "__len__"):
                if len(result) > 0:
                    return result[0]  # type: ignore[return-value]
                return None
            return result  # type: ignore[return-value]
        return None

    async def get_gameclock_by_match(
        self,
        match_id: int,
    ) -> GameClockDB | None:
        self.logger.debug(f"Get match_gameclock by {ITEM} id:{match_id}")
        result = await self.get_related_item_level_one_by_id(
            match_id,
            "match_gameclock",
        )
        if result:
            if hasattr(result, "__len__"):
                if len(result) > 0:
                    return result[0]  # type: ignore[return-value]
                return None
            return result  # type: ignore[return-value]
        return None

    async def get_teams_by_match(
        self,
        match_id: int,
    ) -> dict | None:
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
    ) -> list[PlayerMatchDB]:
        self.logger.debug(f"Get players by {ITEM} id:{match_id}")
        try:
            async with self.db.async_session() as session:
                stmt = select(PlayerMatchDB).where(PlayerMatchDB.match_id == match_id)

                results = await session.execute(stmt)
                players = results.scalars().all()
                return players
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Error getting players for {ITEM} id:{match_id} {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error fetching players for match {match_id}",
            )
        except Exception as ex:
            self.logger.error(
                f"Error getting players for {ITEM} id:{match_id} {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error fetching players for match {match_id}",
            )

    async def get_player_by_match_full_data(self, match_id: int) -> list[dict]:
        self.logger.debug(f"Get players with full data by {ITEM} id:{match_id}")
        try:
            from src.core.models.player import PlayerDB
            from src.core.models.player_team_tournament import PlayerTeamTournamentDB

            async with self.db.async_session() as session:
                stmt = (
                    select(PlayerMatchDB)
                    .where(PlayerMatchDB.match_id == match_id)
                    .options(
                        selectinload(PlayerMatchDB.player_team_tournament)
                        .selectinload(PlayerTeamTournamentDB.player)
                        .selectinload(PlayerDB.person),
                        selectinload(PlayerMatchDB.match_position),
                        selectinload(PlayerMatchDB.team),
                    )
                )

                results = await session.execute(stmt)
                players = results.scalars().all()

                players_with_data = []
                for player in players:
                    players_with_data.append(
                        {
                            "match_player": player,
                            "player_team_tournament": player.player_team_tournament,
                            "person": (
                                player.player_team_tournament.player.person
                                if player.player_team_tournament
                                and player.player_team_tournament.player
                                else None
                            ),
                            "position": player.match_position,
                        }
                    )

                return players_with_data
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Error getting players with full data for {ITEM} id:{match_id} {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error fetching players with full data for match {match_id}",
            )
        except Exception as ex:
            self.logger.error(
                f"Error getting players with full data for {ITEM} id:{match_id} {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error fetching players with full data for match {match_id}",
            )

    async def get_scoreboard_by_match(
        self,
        match_id: int,
    ) -> ScoreboardDB | None:
        self.logger.debug(f"Getting scoreboard for {ITEM} id:{match_id}")
        try:
            result = await self.get_related_item_level_one_by_id(
                match_id,
                "match_scoreboard",
            )
            self.logger.debug(f"Got scoreboard successfully. Result: {result}")
            if result:
                if hasattr(result, "__len__"):
                    if len(result) > 0:
                        return result[0]  # type: ignore[return-value]
                    return None
                return result  # type: ignore[return-value]
            return None
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
