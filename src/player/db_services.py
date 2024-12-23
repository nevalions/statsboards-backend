from fastapi import HTTPException

from src.core.models import BaseServiceDB, PlayerDB
from .schemas import PlayerSchemaCreate, PlayerSchemaUpdate, PlayerSchema


class PlayerServiceDB(BaseServiceDB):
    def __init__(
        self,
        database,
    ):
        super().__init__(database, PlayerDB)

    async def create_or_update_player(
        self,
        p: PlayerSchemaCreate | PlayerSchemaUpdate,
    ):
        try:
            if p.player_eesl_id:
                player_from_db = await self.get_player_by_eesl_id(p.player_eesl_id)
                if player_from_db:
                    # print("updating player", player_from_db)
                    return await self.update_player_by_eesl(
                        "player_eesl_id",
                        p,
                    )
                else:
                    # print("updating player", p)
                    return await self.create_new_player(
                        p,
                    )
            else:
                # print("updating player", p)
                return await self.create_new_player(
                    p,
                )
        except Exception as ex:
            print(ex)
            raise HTTPException(
                status_code=409,
                detail=f"Player eesl " f"id({p}) " f"returned some error",
            )

    async def update_player_by_eesl(
        self,
        eesl_field_name: str,
        p: PlayerSchemaUpdate,
    ):
        return await self.update_item_by_eesl_id(
            eesl_field_name,
            p.player_eesl_id,
            p,
        )

    async def create_new_player(
        self,
        p: PlayerSchemaCreate,
    ):
        player = self.model(
            sport_id=p.sport_id,
            person_id=p.person_id,
            player_eesl_id=p.player_eesl_id,
        )

        print("player", player)
        return await super().create(player)

    async def get_player_by_eesl_id(
        self,
        value,
        field_name="player_eesl_id",
    ):
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def get_player_with_person(self, player_id) -> PlayerSchema:
        return await self.get_related_item_level_one_by_id(player_id, "person")

    async def update_player(
        self,
        item_id: int,
        item: PlayerSchemaUpdate,
        **kwargs,
    ):
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
