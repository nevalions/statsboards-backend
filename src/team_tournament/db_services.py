import asyncio

from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import db, BaseServiceDB, TeamTournamentDB, TournamentDB, TeamDB
from .schemas import TeamTournamentSchemaCreate, TeamTournamentSchemaUpdate


class TeamTournamentServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, TeamTournamentDB)

    async def create_team_tournament_relation(self, te_to: TeamTournamentSchemaCreate):
        if te_to:
            is_exist = await super().is_relation_exist(
                te_to.team_id, te_to.tournament_id, "team_id", "tournament_id"
            )
            if not is_exist:
                relation_ = self.model(
                    team_id=te_to.team_id,
                    tournament_id=te_to.tournament_id,
                )
                relation_ = await super().create(relation_)
                print(
                    f"Relation Team id({relation_.team_id}) "
                    f"Tournament id({relation_.tournament_id}) created"
                )
                return relation_
            else:
                print(
                    f"Relation Team id({te_to.team_id}) "
                    f"Tournament id({te_to.tournament_id}) "
                    f"already exist"
                )

    async def update_team_tournament(
        self, item_id: int, item: TeamTournamentSchemaUpdate, **kwargs
    ):
        return await super().update(item_id, item, **kwargs)

    async def get_teams_by_tournament(
        self,
        tournament_id: int,
        order_by: str = "id",
        descending: bool = False,
        skip: int = 0,
        limit: int = 100,
    ):
        async with self.db.async_session() as session:
            stmt = (
                select(TeamDB)
                .join(TeamTournamentDB)
                .join(TournamentDB)
                .where(TournamentDB.id == tournament_id)
                .offset(skip)
                .limit(limit)
            )

            result = await session.execute(stmt)
            teams = []
            for s in result.scalars().fetchall():
                teams.append(s.__dict__)

            sorted_teams = sorted(
                teams, key=lambda x: x[f"{order_by}"], reverse=descending
            )
            return sorted_teams


async def get_team_tour_db() -> TeamTournamentServiceDB:
    yield TeamTournamentServiceDB(db)


async def async_main() -> None:
    team_service = TeamTournamentServiceDB(db)
    # dict_conv = TeamTournamentSchemaCreate(**{'fk_team': 8, 'fk_tournament': 3})
    # t = await team_service.create_team_tournament_relation(dict_conv)
    t = await team_service.get_teams_by_tournament(2)
    if t:
        print(t)
    else:
        pass


if __name__ == "__main__":
    asyncio.run(async_main())
