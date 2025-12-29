import asyncio

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

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

    async def create(
        self,
        item: TeamTournamentSchemaCreate,
    ):
        self.logger.debug(f"Creat {ITEM} relation:{item}")
        is_relation_exist = await self.get_team_tournament_relation(
            item.team_id,
            item.tournament_id,
        )
        if is_relation_exist:
            return is_relation_exist
        new_team_tournament = self.model(
            team_id=item.team_id,
            tournament_id=item.tournament_id,
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
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as e:
            self.logger.error(
                f"Error on get_team_tournament_relation {e}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error fetching team tournament relation",
            )
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as e:
            self.logger.error(
                f"Error on delete_relation_by_team_and_tournament_id: {e}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error deleting team tournament relation",
            )
        except Exception as e:
            self.logger.error(
                f"Error on delete_relation_by_team_and_tournament_id: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error deleting team tournament relation",
            )
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error fetching team tournament relation",
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
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Error on get_related_teams: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error fetching related teams for tournament {tournament_id}",
            )
        except Exception as ex:
            self.logger.error(
                f"Error on get_related_teams: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error fetching related teams for tournament {tournament_id}",
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
