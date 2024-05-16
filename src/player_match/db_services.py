from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import BaseServiceDB, PlayerMatchDB
from .schemas import PlayerMatchSchemaCreate, PlayerMatchSchemaUpdate
from ..player.db_services import PlayerServiceDB


class PlayerMatchServiceDB(BaseServiceDB):
    def __init__(
            self,
            database,
    ):
        super().__init__(database, PlayerMatchDB)

    async def create_or_update_player_match(
            self,
            p: PlayerMatchSchemaCreate | PlayerMatchSchemaUpdate,
    ):
        try:
            if p.player_match_eesl_id:
                player_match_from_db = await self.get_player_match_by_eesl_id(
                    p.player_match_eesl_id)
                if player_match_from_db:
                    # print('player updating')
                    return await self.update_player_match_by_eesl(
                        "player_match_eesl_id",
                        p,
                    )
                else:
                    # print('player creating')
                    return await self.create_new_player_match(
                        p,
                    )
            else:
                if p.match_id and p.player_team_tournament_id:
                    player_match_from_db = await self.get_players_match_by_match_id(
                        p.match_id,
                        p.player_team_tournament_id
                    )
                    if player_match_from_db:
                        # print('player updating')
                        return await self.update_player_match(player_match_from_db.id, p)
                # print('player creating')
                return await self.create_new_player_match(
                    p,
                )


        except Exception as ex:
            print(ex)
            raise HTTPException(
                status_code=409,
                detail=f"Player_match " f"id({p}) " f"returned some error",
            )

    async def update_player_match_by_eesl(
            self,
            eesl_field_name: str,
            p: PlayerMatchSchemaUpdate,
    ):
        return await self.update_item_by_eesl_id(
            eesl_field_name,
            p.player_match_eesl_id,
            p,
        )

    async def create_new_player_match(
            self,
            p: PlayerMatchSchemaCreate,
    ):

        player_match = self.model(
            player_match_eesl_id=p.player_match_eesl_id,
            player_team_tournament_id=p.player_team_tournament_id,
            match_position=p.match_position,
            match_id=p.match_id,
            match_number=p.match_number,
        )

        # print('player_match', player_match)
        return await super().create(player_match)

    async def get_player_match_by_eesl_id(
            self,
            value,
            field_name="player_match_eesl_id",
    ):
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def get_players_match_by_match_id(
            self,
            match_id,
            player_team_tournament_id
    ):
        async with self.db.async_session() as session:
            stmt = (
                select(PlayerMatchDB)
                .where(PlayerMatchDB.match_id == match_id)
                .where(PlayerMatchDB.player_team_tournament_id == player_team_tournament_id)
            )

            results = await session.execute(stmt)
            players = results.scalars().one_or_none()
            return players

    # async def get_player_match_with_person(self, player_id: int):
    #     player_service = PlayerServiceDB(self.db)
    #     return await self.get_nested_related_items_by_id(
    #         player_id,
    #         player_service,
    #         'player',
    #         'person',
    #     )

    async def update_player_match(
            self,
            item_id: int,
            item: PlayerMatchSchemaUpdate,
            **kwargs,
    ):
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
