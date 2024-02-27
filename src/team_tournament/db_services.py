import asyncio

from fastapi import HTTPException
from sqlalchemy import text, select, delete

from src.core.models import db, BaseServiceDB, TeamTournamentDB, TournamentDB, TeamDB
from src.team_tournament.schemas import TeamTournamentSchemaCreate


class TeamTournamentServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, TeamTournamentDB)

    # async def create_team_tournament_relation(
    #         self,
    #         tournament_id: int,
    #         team_id: int,
    #         tournament_id_name: str = "tournament_id",
    #         team_id_name: str = "team_id",
    #         child_relation="teams",
    # ):
    #     return await self.create_m2m_relation(
    #         parent_model=TournamentDB,
    #         child_model=TeamDB,
    #         secondary_table=text("team_tournament"),
    #         parent_id=tournament_id,
    #         child_id=team_id,
    #         parent_id_name=tournament_id_name,
    #         child_id_name=team_id_name,
    #         child_relation=child_relation,
    #     )

    async def create_team_tournament_relation(
            self,
            team_tournament: TeamTournamentSchemaCreate,
    ):
        new_team_tournament = self.model(
            team_id=team_tournament.team_id,
            tournament_id=team_tournament.tournament_id,
        )
        return await super().create(new_team_tournament)

    async def get_team_tournament_relation(self, team_id: int, tournament_id: int):
        async with self.db.async_session() as session:
            result = await session.execute(
                select(TeamTournamentDB).where(
                    (TeamTournamentDB.team_id == team_id) &
                    (TeamTournamentDB.tournament_id == tournament_id)
                )
            )
            team_tournament = result.scalars().first()
            await session.commit()
        return team_tournament

    async def get_related_teams(self, tournament_id: int):
        async with self.db.async_session() as session:
            result = await session.execute(
                select(TeamDB).join(TeamTournamentDB).where(
                    TeamTournamentDB.tournament_id == tournament_id
                )
            )
            teams = result.scalars().all()
            await session.commit()
            return teams

    async def delete_relation_by_team_and_tournament_id(self, team_id: int, tournament_id: int):
        async with self.db.async_session() as session:
            result = await session.execute(
                select(TeamTournamentDB).where(
                    (TeamTournamentDB.team_id == team_id) &
                    (TeamTournamentDB.tournament_id == tournament_id)
                )
            )

            item = result.scalars().first()

            if not item:
                raise HTTPException(
                    status_code=404,
                    detail=f"Connection team id: {team_id} and tournament id {tournament_id} not foutnd"
                )

            await session.delete(item)
            await session.commit()
            raise HTTPException(
                status_code=200,
                detail=f"Connection team id: {team_id} and tournament id {tournament_id} deleted",
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
