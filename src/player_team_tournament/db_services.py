from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import BaseServiceDB, PlayerTeamTournamentDB
from .schemas import PlayerTeamTournamentSchemaCreate, PlayerTeamTournamentSchemaUpdate
from src.player.db_services import PlayerServiceDB


class PlayerTeamTournamentServiceDB(BaseServiceDB):
    def __init__(
        self,
        database,
    ):
        super().__init__(database, PlayerTeamTournamentDB)

    async def create_or_update_player_team_tournament(
        self,
        p: PlayerTeamTournamentSchemaCreate | PlayerTeamTournamentSchemaUpdate,
    ):
        try:
            if p.player_team_tournament_eesl_id:
                player_team_tournament_from_db = (
                    await self.get_player_team_tournament_by_eesl_id(
                        p.player_team_tournament_eesl_id
                    )
                )
                if player_team_tournament_from_db:
                    # print('player updating')
                    return await self.update_player_team_tournament_by_eesl(
                        "player_team_tournament_eesl_id",
                        p,
                    )
                else:
                    # print('player creating')
                    return await self.create_new_player_team_tournament(
                        p,
                    )
            else:
                if p.tournament_id and p.player_id:
                    player_team_tournament_from_db = (
                        await self.get_player_team_tournaments_by_tournament_id(
                            p.tournament_id, p.player_id
                        )
                    )
                    if player_team_tournament_from_db:
                        # print('player updating')
                        return await self.update_player_team_tournament(
                            player_team_tournament_from_db.id, p
                        )
                # print('player creating')
                return await self.create_new_player_team_tournament(
                    p,
                )

        except Exception as ex:
            print(ex)
            raise HTTPException(
                status_code=409,
                detail=f"Player_team_tournament " f"id({p}) " f"returned some error",
            )

    async def update_player_team_tournament_by_eesl(
        self,
        eesl_field_name: str,
        p: PlayerTeamTournamentSchemaUpdate,
    ):
        if p.player_team_tournament_eesl_id is not None and isinstance(
            p.player_team_tournament_eesl_id, int
        ):
            return await self.update_item_by_eesl_id(
                eesl_field_name,
                p.player_team_tournament_eesl_id,
                p,
            )
        raise HTTPException(
            status_code=400,
            detail="Invalid player team tournament EEsl ID",
        )

    async def create_new_player_team_tournament(
        self,
        p: PlayerTeamTournamentSchemaCreate,
    ):
        player_team_tournament = self.model(
            player_team_tournament_eesl_id=p.player_team_tournament_eesl_id,
            player_id=p.player_id,
            position_id=p.position_id,
            team_id=p.team_id,
            tournament_id=p.tournament_id,
            player_number=p.player_number,
        )

        # print('player_team_tournament', player_team_tournament)
        return await super().create(player_team_tournament)

    async def get_player_team_tournament_by_eesl_id(
        self,
        value,
        field_name="player_team_tournament_eesl_id",
    ):
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def get_player_team_tournaments_by_tournament_id(
        self, tournament_id, player_id
    ):
        async with self.db.async_session() as session:
            stmt = (
                select(PlayerTeamTournamentDB)
                .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
                .where(PlayerTeamTournamentDB.player_id == player_id)
            )

            results = await session.execute(stmt)
            players = results.scalars().one_or_none()
            return players

    async def get_player_team_tournament_with_person(self, player_id: int):
        player_service = PlayerServiceDB(self.db)
        return await self.get_nested_related_item_by_id(
            player_id,
            player_service,
            "player",
            "person",
        )

    async def update_player_team_tournament(
        self,
        item_id: int,
        item: PlayerTeamTournamentSchemaUpdate,
        **kwargs,
    ):
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
