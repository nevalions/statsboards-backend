from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.models.base import Database
from src.core.models import BaseServiceDB, TeamDB, PlayerTeamTournamentDB, MatchDB
from src.positions.db_services import PositionServiceDB
from .schemas import TeamSchemaCreate, TeamSchemaUpdate
from ..logging_config import setup_logging, get_logger

setup_logging()
ITEM = "TEAM"


class TeamServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, TeamDB)
        self.logger = get_logger("backend_logger_TeamServiceDB", self)
        self.logger.debug(f"Initialized TeamServiceDB")

    async def create(
        self,
        item: TeamSchemaCreate | TeamSchemaUpdate,
    ) -> TeamDB:
        try:
            team = self.model(
                team_eesl_id=item.team_eesl_id,
                title=item.title,
                city=item.city,
                description=item.description,
                team_logo_url=item.team_logo_url,
                team_logo_icon_url=item.team_logo_icon_url,
                team_logo_web_url=item.team_logo_web_url,
                team_color=item.team_color,
                sponsor_line_id=item.sponsor_line_id,
                main_sponsor_id=item.main_sponsor_id,
                sport_id=item.sport_id,
            )
            self.logger.debug(f"Starting to create TeamDB with data: {team.__dict__}")
            return await super().create(team)
        except Exception as ex:
            self.logger.error(f"Error creating {ITEM} {ex}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"Error creating {self.model.__name__}. Check input data. {ITEM}",
            )

    async def create_or_update_team(
        self,
        t: TeamSchemaCreate | TeamSchemaUpdate,
    ) -> TeamDB:
        return await super().create_or_update(t, eesl_field_name="team_eesl_id")

    async def get_team_by_eesl_id(
        self,
        value: int | str,
        field_name: str = "team_eesl_id",
    ) -> TeamDB | None:
        self.logger.debug(f"Get {ITEM} {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def get_matches_by_team_id(
        self,
        team_id: int,
    ) -> list[MatchDB]:
        self.logger.debug(f"Get matches by {ITEM} id:{team_id}")
        return await self.get_related_item_level_one_by_id(
            team_id,
            "matches",
        )

    async def get_players_by_team_id_tournament_id(
        self,
        team_id: int,
        tournament_id: int,
    ) -> list[PlayerTeamTournamentDB]:
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
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Error on get_players_by_team_id_tournament_id: {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error fetching players for team {team_id} and tournament {tournament_id}",
            )
        except Exception as ex:
            self.logger.error(
                f"Error on get_players_by_team_id_tournament_id: {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error fetching players",
            )

    async def get_players_by_team_id_tournament_id_with_person(
        self,
        team_id: int,
        tournament_id: int,
    ) -> list[dict]:
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
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Error on get_players_by_team_id_tournament_id_with_person: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error fetching players with person data",
            )
        except Exception as ex:
            self.logger.error(
                f"Error on get_players_by_team_id_tournament_id_with_person: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error fetching players with person data",
            )

    async def update(
        self,
        item_id: int,
        item: TeamSchemaUpdate,
        **kwargs,
    ) -> TeamDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
