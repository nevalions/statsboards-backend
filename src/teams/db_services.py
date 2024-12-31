import asyncio

from fastapi import HTTPException, UploadFile
from sqlalchemy import select

from src.core.models import db, BaseServiceDB, TeamDB, PlayerTeamTournamentDB
from src.positions.db_services import PositionServiceDB
from .schemas import TeamSchemaCreate, TeamSchemaUpdate
from ..logging_config import setup_logging, get_logger

setup_logging()
ITEM = "TEAM"


class TeamServiceDB(BaseServiceDB):
    def __init__(
        self,
        database,
    ):
        super().__init__(database, TeamDB)
        self.logger = get_logger("backend_logger_TeamServiceDB", self)
        self.logger.debug(f"Initialized TeamServiceDB")

    async def create_or_update_team(
        self,
        t: TeamSchemaCreate | TeamSchemaUpdate,
    ):
        try:
            self.logger.debug(f"Creat or update {ITEM}:{t}")
            if t.team_eesl_id:
                self.logger.debug(f"Get {ITEM} eesl_id:{t.team_eesl_id}")
                team_from_db = await self.get_team_by_eesl_id(t.team_eesl_id)
                if team_from_db:
                    self.logger.debug(
                        f"{ITEM} eesl_id:{t.team_eesl_id} already exists updating"
                    )
                    return await self.update_team_by_eesl(
                        "team_eesl_id",
                        t,
                    )
                else:
                    return await self.create_new_team(t)
            else:
                return await self.create_new_team(t)
        except Exception as ex:
            self.logger.error(f"{ITEM} returned an error: {ex}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"{ITEM} ({t}) returned some error",
            )

    async def update_team_by_eesl(
        self,
        eesl_field_name: str,
        t: TeamSchemaUpdate,
    ):
        self.logger.debug(f"Update {ITEM} {eesl_field_name}:{t.team_eesl_id}")
        return await self.update_item_by_eesl_id(
            eesl_field_name,
            t.team_eesl_id,
            t,
        )

    async def create_new_team(
        self,
        t: TeamSchemaCreate,
    ):
        team = self.model(
            sport_id=t.sport_id,
            city=t.city,
            team_eesl_id=t.team_eesl_id,
            title=t.title,
            description=t.description,
            team_logo_url=t.team_logo_url,
            team_logo_icon_url=t.team_logo_icon_url,
            team_logo_web_url=t.team_logo_web_url,
            team_color=t.team_color,
            sponsor_line_id=t.sponsor_line_id,
            main_sponsor_id=t.main_sponsor_id,
        )

        self.logger.debug(f"Create new {ITEM}:{t}")
        return await super().create(team)

    async def get_team_by_eesl_id(
        self,
        value,
        field_name="team_eesl_id",
    ):
        self.logger.debug(f"Get {ITEM} {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def get_matches_by_team_id(
        self,
        team_id: int,
    ):
        self.logger.debug(f"Get matches by {ITEM} id:{team_id}")
        return await self.get_related_item_level_one_by_id(
            team_id,
            "matches",
        )

    async def get_players_by_team_id_tournament_id(
        self,
        team_id: int,
        tournament_id: int,
    ):
        self.logger.debug(
            f"Get players by {ITEM} id:{team_id} and tournament id:{tournament_id}"
        )
        try:
            async with self.db.async_session() as session:
                stmt = (
                    select(PlayerTeamTournamentDB)
                    .where(PlayerTeamTournamentDB.team_id == team_id)
                    .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
                )

                results = await session.execute(stmt)
                players = results.scalars().all()
                return players
        except Exception as ex:
            self.logger.error(
                f"Error on get_players_by_team_id_tournament_id: {ex}", exc_info=True
            )

    async def get_players_by_team_id_tournament_id_with_person(
        self,
        team_id: int,
        tournament_id: int,
    ):
        self.logger.debug(
            f"Get players with person by {ITEM} id:{team_id} and tournament id:{tournament_id}"
        )
        try:
            from src.player_team_tournament.db_services import (
                PlayerTeamTournamentServiceDB,
            )

            player_service = PlayerTeamTournamentServiceDB(self.db)
            position_service = PositionServiceDB(self.db)
            players = await self.get_players_by_team_id_tournament_id(
                team_id, tournament_id
            )

            players_full_data = []
            if players:
                for p in players:
                    person = (
                        await player_service.get_player_team_tournament_with_person(
                            p.id
                        )
                    )
                    position = await position_service.get_by_id(p.position_id)
                    # players_full_data.append(person)
                    # players_full_data.append(p)
                    player_full_data = {
                        "player_team_tournament": p,
                        "person": person,
                        "position": position,
                    }
                    players_full_data.append(player_full_data)
                return players_full_data
        except Exception as ex:
            self.logger.error(
                f"Error on get_players_by_team_id_tournament_id_with_person: {ex}",
                exc_info=True,
            )

    async def update_team(
        self,
        item_id: int,
        item: TeamSchemaUpdate,
        **kwargs,
    ):
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
