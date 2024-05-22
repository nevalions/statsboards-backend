import asyncio

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload

from src.core.models import db, BaseServiceDB, MatchDB, TeamDB, PlayerMatchDB
from src.player_match.db_services import PlayerMatchServiceDB
from .shemas import MatchSchemaCreate, MatchSchemaUpdate


class MatchServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, MatchDB)

    async def create_or_update_match(self, m: MatchSchemaCreate):
        try:
            if m.match_eesl_id:
                match_from_db = await self.get_match_by_eesl_id(m.match_eesl_id)
                if match_from_db:
                    return await self.update_match_by_eesl(
                        "match_eesl_id",
                        m,
                    )
                else:
                    return await self.create_new_match(m)
            else:
                return await self.create_new_match(m)
        except Exception as ex:
            print(ex)
            raise HTTPException(
                status_code=409,
                detail=f"Match " f"id({m}) " f"returned some error",
            )

    async def update_match_by_eesl(
        self,
        eesl_field_name: str,
        m: MatchSchemaCreate,
    ):
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
            main_sponsor=m.main_sponsor,
            sponsor_line=m.sponsor_line,
        )
        return await super().create(match)

    async def get_match_by_eesl_id(
        self,
        value,
        field_name="match_eesl_id",
    ):
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
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    async def get_match_sponsor_line(self, match_id: int):
        return await self.get_related_items_level_one_by_id(match_id, "sponsor_line")

    async def get_matchdata_by_match(
        self,
        match_id: int,
    ):
        return await self.get_related_items_level_one_by_id(
            match_id,
            "match_data",
        )

    async def get_playclock_by_match(
        self,
        match_id: int,
    ):
        return await self.get_related_items_level_one_by_id(
            match_id,
            "match_playclock",
        )

    async def get_gameclock_by_match(
        self,
        match_id: int,
    ):
        return await self.get_related_items_level_one_by_id(
            match_id,
            "match_gameclock",
        )

    async def get_teams_by_match(
        self,
        match_id: int,
    ):
        match = await self.get_related_items(
            match_id,
        )

        if match:
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

        return None

    async def get_players_by_match(
        self,
        match_id: int,
    ):
        async with self.db.async_session() as session:
            stmt = select(PlayerMatchDB).where(PlayerMatchDB.match_id == match_id)

            results = await session.execute(stmt)
            players = results.scalars().all()
            return players

    async def get_player_by_match_full_data(self, match_id: int):
        player_service = PlayerMatchServiceDB(self.db)
        players = await self.get_players_by_match(match_id)
        players_with_data = []
        if players:
            for player in players:
                p = await player_service.get_player_in_match_full_data(player.id)
                players_with_data.append(p)
            return players_with_data
        return players_with_data

    async def get_scoreboard_by_match(
        self,
        match_id: int,
    ):
        return await self.get_related_items_level_one_by_id(
            match_id,
            "match_scoreboard",
        )


async def get_match_db() -> MatchServiceDB:
    yield MatchServiceDB(db)


async def async_main() -> None:
    match_service = MatchServiceDB(db)
    # t = await team_service.get_team_by_id(1)
    # t = await team_service.find_team_tournament_relation(6, 2)
    # print(t)
    # t = await team_service.get_team_by_eesl_id(1)
    # u = await match_service.create_match()
    # if t:
    #     print(t.__dict__)


if __name__ == "__main__":
    asyncio.run(async_main())
