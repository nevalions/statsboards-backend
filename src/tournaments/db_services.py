from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.models.base import Database
from src.core.models import BaseServiceDB, PlayerTeamTournamentDB, TournamentDB, TeamDB, MatchDB, SponsorDB, SponsorLineDB

from ..logging_config import get_logger, setup_logging
from ..sponsor_lines.db_services import SponsorLineServiceDB
from .schemas import TournamentSchemaCreate, TournamentSchemaUpdate

setup_logging()
ITEM = "TOURNAMENT"


class TournamentServiceDB(BaseServiceDB):
    def __init__(self, database: Database) -> None:
        super().__init__(
            database,
            TournamentDB,
        )
        self.logger = get_logger("backend_logger_TournamentServiceDB", self)
        self.logger.debug("Initialized TournamentServiceDB")

    async def create(
        self,
        item: TournamentSchemaCreate | TournamentSchemaUpdate,
    ) -> TournamentDB:
        try:
            tournament = self.model(
                title=item.title,
                description=item.description,
                tournament_logo_url=item.tournament_logo_url,
                tournament_logo_icon_url=item.tournament_logo_icon_url,
                tournament_logo_web_url=item.tournament_logo_web_url,
                season_id=item.season_id,
                sport_id=item.sport_id,
                main_sponsor_id=item.main_sponsor_id,
                sponsor_line_id=item.sponsor_line_id,
                tournament_eesl_id=item.tournament_eesl_id,
            )
            self.logger.debug(f"Create new {ITEM}:{tournament}")
            return await super().create(tournament)
        except Exception as ex:
            self.logger.error(f"Error creating {ITEM} {ex}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"Error creating {self.model.__name__}. Check input data. {ITEM}",
            )

    async def create_or_update_tournament(
        self,
        t: TournamentSchemaCreate | TournamentSchemaUpdate,
    ) -> TournamentDB:
        return await super().create_or_update(t, eesl_field_name="tournament_eesl_id")

    async def get_tournament_by_eesl_id(
        self,
        value: int | str,
        field_name: str = "tournament_eesl_id",
    ) -> TournamentDB | None:
        self.logger.debug(f"Get {ITEM} {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def update(
        self,
        item_id: int,
        item: TournamentSchemaUpdate,
        **kwargs,
    ) -> TournamentDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    async def get_teams_by_tournament(
        self,
        tournament_id: int,
    ) -> list[TeamDB]:
        self.logger.debug(f"Get teams by {ITEM} id:{tournament_id}")
        return await self.get_related_item_level_one_by_id(
            tournament_id,
            "teams",
        )

    # async def get_players_by_tournament(
    #         self,
    #         tournament_id: int,
    # ):
    #     return await self.get_related_items_level_one_by_id(
    #         tournament_id,
    #         "players_team_tournament",
    #     )

    async def get_players_by_tournament(
        self,
        tournament_id: int,
    ) -> list[PlayerTeamTournamentDB]:
        self.logger.debug(f"Get players by {ITEM} id:{tournament_id}")
        try:
            async with self.db.async_session() as session:
                stmt = select(PlayerTeamTournamentDB).where(
                    PlayerTeamTournamentDB.tournament_id == tournament_id
                )

                results = await session.execute(stmt)
                players = results.scalars().all()
                return players
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Error on get_players_by_tournament: {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error fetching players for tournament {tournament_id}",
            )
        except Exception as ex:
            self.logger.error(
                f"Error on get_players_by_tournament: {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error fetching players for tournament {tournament_id}",
            )

    async def get_count_of_matches_by_tournament(
        self,
        tournament_id: int,
    ) -> int:
        self.logger.debug(f"Get matches by {ITEM} id:{tournament_id}")
        return await self.get_count_of_items_level_one_by_id(
            tournament_id,
            "matches",
        )

    async def get_matches_by_tournament(
        self,
        tournament_id: int,
    ) -> list[MatchDB]:
        self.logger.debug(f"Get matches by {ITEM} id:{tournament_id}")
        return await self.get_related_item_level_one_by_id(
            tournament_id,
            "matches",
        )

    async def get_matches_by_tournament_with_pagination(
        self,
        tournament_id: int,
        skip: int = 0,
        limit: int = 20,
        order_exp: str = "id",
        order_exp_two: str = "id",
    ) -> list[MatchDB]:
        self.logger.debug(
            f"Get matches by {ITEM} id:{tournament_id} with pagination: skip={skip}, limit={limit}"
        )
        return await self.get_related_item_level_one_by_id(
            tournament_id,
            "matches",
            skip=skip,
            limit=limit,
            order_by=order_exp,
            order_by_two=order_exp_two,
        )

    async def get_main_tournament_sponsor(self, tournament_id: int) -> SponsorDB | None:
        self.logger.debug(f"Get main tournament's sponsor by {ITEM} id:{tournament_id}")
        return await self.get_related_item_level_one_by_id(
            tournament_id, "main_sponsor"
        )

    async def get_tournament_sponsor_line(self, tournament_id: int) -> SponsorLineDB | None:
        self.logger.debug(f"Get tournament's sponsor line by {ITEM} id:{tournament_id}")
        return await self.get_related_item_level_one_by_id(
            tournament_id, "sponsor_line"
        )

    async def get_sponsors_of_tournament_sponsor_line(self, tournament_id: int) -> list[SponsorDB]:
        sponsor_service = SponsorLineServiceDB(self.db)
        self.logger.debug(
            f"Get sponsors of tournament sponsor line {ITEM} id:{tournament_id}"
        )
        return await self.get_nested_related_item_by_id(
            tournament_id,
            sponsor_service,
            "sponsor_line",
            "sponsors",
        )

    # async def get_sponsors_of_tournament_sponsor_line(self, tournament_id: int):
    #     sponsor_line = await self.get_related_items_level_one_by_id(
    #         tournament_id,
    #         'sponsor_line'
    #     )
    #
    #     if sponsor_line is not None:
    #         sponsor_line_id = sponsor_line.id
    #         sponsor_service = SponsorLineServiceDB(self.db)
    #         sponsors = await sponsor_service.get_related_items_level_one_by_id(
    #             sponsor_line_id,
    #             'sponsors'
    #         )
    #         return sponsors
    #
    #     return []

    # async def get_sponsors_of_tournament_sponsor_line(self, tournament_id: int):
    #     return await self.get_related_items_level_one_by_id(
    #         tournament_id,
    #         'sponsor_line',
    #         'sponsors'
    #     )
