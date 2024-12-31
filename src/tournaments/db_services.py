from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import db, BaseServiceDB, TournamentDB, PlayerTeamTournamentDB
from .schemas import TournamentSchemaCreate, TournamentSchemaUpdate
from ..logging_config import setup_logging, get_logger
from ..sponsor_lines.db_services import SponsorLineServiceDB

setup_logging()


class TournamentServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(
            database,
            TournamentDB,
        )
        self.logger = get_logger("backend_logger_TournamentServiceDB", self)

    async def create_or_update_tournament(
        self,
        t: TournamentSchemaCreate | TournamentSchemaUpdate,
    ):
        try:
            # Try to query for existing item
            self.logger.debug(f"Creat or update tournament:{t}")
            if t.tournament_eesl_id:
                self.logger.debug(f"Get tournament eesl_id:{t.tournament_eesl_id}")
                tournament_from_db = await self.get_tournament_by_eesl_id(
                    t.tournament_eesl_id
                )
                if tournament_from_db:
                    self.logger.debug(
                        f"Tournament eesl_id:{t.tournament_eesl_id} already exists updating"
                    )
                    return await self.update_tournament_by_eesl(
                        "tournament_eesl_id",
                        t,
                    )
                else:
                    return await self.create_new_tournament(t)
            else:
                print("Creating new tournament")
                return await self.create_new_tournament(t)
        except Exception as ex:
            print(ex)
            raise HTTPException(
                status_code=409,
                detail=f"Tournament eesl id:({t}) returned some error",
            )

    async def update_tournament_by_eesl(
        self,
        eesl_field_name: str,
        t: TournamentSchemaUpdate,
    ):
        return await self.update_item_by_eesl_id(
            eesl_field_name,
            t.tournament_eesl_id,
            t,
        )

    async def create_new_tournament(
        self,
        t: TournamentSchemaCreate,
    ):
        tournament = self.model(
            title=t.title,
            description=t.description,
            tournament_logo_url=t.tournament_logo_url,
            tournament_logo_icon_url=t.tournament_logo_icon_url,
            tournament_logo_web_url=t.tournament_logo_web_url,
            season_id=t.season_id,
            sport_id=t.sport_id,
            main_sponsor_id=t.main_sponsor_id,
            sponsor_line_id=t.sponsor_line_id,
            tournament_eesl_id=t.tournament_eesl_id,
        )
        self.logger.debug(f"Create new tournament:{tournament}")
        return await super().create(tournament)

    async def get_tournament_by_eesl_id(
        self,
        value,
        field_name="tournament_eesl_id",
    ):
        self.logger.debug(f"Get tournament {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def update_tournament(
        self,
        item_id: int,
        item: TournamentSchemaUpdate,
        **kwargs,
    ):
        self.logger.debug(f"Update tournament:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    async def get_teams_by_tournament(
        self,
        tournament_id: int,
    ):
        self.logger.debug(f"Get teams by tournament id:{tournament_id}")
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
    ):
        self.logger.debug(f"Get players by tournament id:{tournament_id}")
        async with self.db.async_session() as session:
            stmt = select(PlayerTeamTournamentDB).where(
                PlayerTeamTournamentDB.tournament_id == tournament_id
            )

            results = await session.execute(stmt)
            players = results.scalars().all()
            return players

    async def get_matches_by_tournament(
        self,
        tournament_id: int,
    ):
        self.logger.debug(f"Get matches by tournament id:{tournament_id}")
        return await self.get_related_item_level_one_by_id(
            tournament_id,
            "matches",
        )

    async def get_main_tournament_sponsor(self, tournament_id: int):
        self.logger.debug(
            f"Get main tournament's sponsor by tournament id:{tournament_id}"
        )
        return await self.get_related_item_level_one_by_id(
            tournament_id, "main_sponsor"
        )

    async def get_tournament_sponsor_line(self, tournament_id: int):
        self.logger.debug(
            f"Get tournament's sponsor line by tournament id:{tournament_id}"
        )
        return await self.get_related_item_level_one_by_id(
            tournament_id, "sponsor_line"
        )

    async def get_sponsors_of_tournament_sponsor_line(self, tournament_id: int):
        sponsor_service = SponsorLineServiceDB(self.db)
        self.logger.debug(
            f"Get sponsors of tournament sponsor line tournament id:{tournament_id}"
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
