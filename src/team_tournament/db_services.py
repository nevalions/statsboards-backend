import asyncio

from sqlalchemy import text

from src.core.models import db, BaseServiceDB, TeamTournamentDB, TournamentDB, TeamDB


class TeamTournamentServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, TeamTournamentDB)

    async def create_team_tournament_relation(
        self,
        tournament_id: int,
        team_id: int,
        tournament_id_name: str = "tournament_id",
        team_id_name: str = "team_id",
        child_relation="teams",
    ):
        return await self.create_m2m_relation(
            parent_model=TournamentDB,
            child_model=TeamDB,
            secondary_table=text("team_tournament"),
            parent_id=tournament_id,
            child_id=team_id,
            parent_id_name=tournament_id_name,
            child_id_name=team_id_name,
            child_relation=child_relation,
        )


async def get_team_tour_db() -> TeamTournamentServiceDB:
    yield TeamTournamentServiceDB(db)


async def async_main() -> None:
    team_service = TeamTournamentServiceDB(db)
    # dict_conv = TeamTournamentSchemaCreate(**{'fk_team': 8, 'fk_tournament': 3})
    # t = await team_service.create_team_tournament_relation(dict_conv)
    # t = await team_service.get_teams_by_tournament(3)
    # if t:
    #     print(t)
    # else:
    #     pass


if __name__ == "__main__":
    asyncio.run(async_main())
