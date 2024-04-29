import asyncio

from fastapi import HTTPException

from src.core.models import db, BaseServiceDB, TournamentDB
from .schemas import TournamentSchemaCreate, TournamentSchemaUpdate
from ..sponsor_lines.db_services import SponsorLineServiceDB
from ..sponsors.db_services import SponsorServiceDB


class TournamentServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(
            database,
            TournamentDB,
        )

    async def create_or_update_tournament(
            self,
            t: TournamentSchemaCreate | TournamentSchemaUpdate,
    ):
        try:
            # Try to query for existing item
            if t.tournament_eesl_id:
                print('EESL ID', t.tournament_eesl_id)
                tournament_from_db = await self.get_tournament_by_eesl_id(
                    t.tournament_eesl_id
                )
                if tournament_from_db:
                    print('Tournament already exist')
                    return await self.update_tournament_by_eesl(
                        "tournament_eesl_id",
                        t,
                    )
                else:
                    return await self.create_new_tournament(t)
            else:
                print('Creating new tournament')
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
            season_id=t.season_id,
            sport_id=t.sport_id,
            main_sponsor_id=t.main_sponsor_id,
            sponsor_line_id=t.sponsor_line_id,
            tournament_eesl_id=t.tournament_eesl_id,
        )
        return await super().create(tournament)

    async def get_tournament_by_eesl_id(
            self,
            value,
            field_name="tournament_eesl_id",
    ):
        print('Getting tournament with eesl_id', value, field_name)
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
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    async def get_teams_by_tournament(
            self,
            tournament_id: int,
    ):
        return await self.get_related_items_level_one_by_id(
            tournament_id,
            "teams",
        )

    async def get_matches_by_tournament(
            self,
            tournament_id: int,
    ):
        return await self.get_related_items_level_one_by_id(
            tournament_id,
            "matches",
        )

    async def get_main_tournament_sponsor(self, tournament_id: int):
        return await self.get_related_items_level_one_by_id(
            tournament_id,
            'main_sponsor'
        )

    async def get_tournament_sponsor_line(self, tournament_id: int):
        return await self.get_related_items_level_one_by_id(
            tournament_id,
            'sponsor_line'
        )

    async def get_sponsors_of_tournament_sponsor_line(self, tournament_id: int):
        sponsor_service = SponsorLineServiceDB(self.db)
        return await self.get_nested_related_items_by_id(
            tournament_id,
            sponsor_service,
            'sponsor_line',
            'sponsors',
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

#
# async def get_tournament_db() -> TournamentServiceDB:
#     yield TournamentServiceDB(db)
#
#
# async def async_main() -> None:
#     tournament_service = TournamentServiceDB(db)
#     # t = await tournament_service.get_tournaments_by_year(2222)
#     # print(t)
#     # print(t.__dict__)
#
#
# if __name__ == "__main__":
#     asyncio.run(async_main())
