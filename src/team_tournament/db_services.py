import asyncio

from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import db, BaseServiceDB, TeamTournamentDB, TeamDB
from src.logging_config import setup_logging, get_logger
from src.team_tournament.schemas import TeamTournamentSchemaCreate

setup_logging()
ITEM = "TEAM_TOURNAMENT"


class TeamTournamentServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, TeamTournamentDB)
        self.logger = get_logger("backend_logger_TeamTournamentServiceDB", self)
        self.logger.debug(f"Initialized TeamTournamentServiceDB")

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
        self.logger.debug(f"Creat {ITEM} relation:{team_tournament}")
        is_relation_exist = await self.get_team_tournament_relation(
            team_tournament.team_id,
            team_tournament.tournament_id,
        )
        if is_relation_exist:
            return is_relation_exist
        new_team_tournament = self.model(
            team_id=team_tournament.team_id,
            tournament_id=team_tournament.tournament_id,
        )
        return await super().create(new_team_tournament)

    async def get_team_tournament_relation(self, team_id: int, tournament_id: int):
        try:
            self.logger.debug(
                f"Get {ITEM} relation: team_id:{team_id} tournament_id:{tournament_id}"
            )
            async with self.db.async_session() as session:
                result = await session.execute(
                    select(TeamTournamentDB).where(
                        (TeamTournamentDB.team_id == team_id)
                        & (TeamTournamentDB.tournament_id == tournament_id)
                    )
                )
                team_tournament = result.scalars().first()
                await session.commit()
            return team_tournament
        except Exception as e:
            self.logger.error(
                f"Error on get_team_tournament_relation {e}", exc_info=True
            )

    async def get_related_teams(self, tournament_id: int):
        try:
            self.logger.debug(
                f"Get {ITEM} related teams for tournament_id:{tournament_id}"
            )
            async with self.db.async_session() as session:
                result = await session.execute(
                    select(TeamDB)
                    .join(TeamTournamentDB)
                    .where(TeamTournamentDB.tournament_id == tournament_id)
                )
                teams = result.scalars().all()
                await session.commit()
                return teams
        except Exception as ex:
            self.logger.error(
                f"Error on get_related_teams: {ex}",
                exc_info=True,
            )

    async def delete_relation_by_team_and_tournament_id(
        self, team_id: int, tournament_id: int
    ):
        try:
            self.logger.debug(
                f"Delete {ITEM} team_id:{team_id} tournament_id:{tournament_id}"
            )
            async with self.db.async_session() as session:
                result = await session.execute(
                    select(TeamTournamentDB).where(
                        (TeamTournamentDB.team_id == team_id)
                        & (TeamTournamentDB.tournament_id == tournament_id)
                    )
                )
                item = result.scalars().first()
            await session.delete(item)
            await session.commit()
        except Exception as ex:
            self.logger.error(
                f"Error on delete_relation_by_team_and_tournament_id: {ex}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Error on delete connection team id: {team_id} and tournament id {tournament_id}",
            )


# async def get_team_tour_db() -> TeamTournamentServiceDB:
#     yield TeamTournamentServiceDB(db)
#
#
# async def async_main() -> None:
#     team_service = TeamTournamentServiceDB(db)
#     # dict_conv = TeamTournamentSchemaCreate(**{'fk_team': 8, 'fk_tournament': 3})
#     # t = await team_service.create_team_tournament_relation(dict_conv)
#     # t = await team_service.get_teams_by_tournament(3)
#     # if t:
#     #     print(t)
#     # else:
#     #     pass
#
#
# if __name__ == "__main__":
#     asyncio.run(async_main())
