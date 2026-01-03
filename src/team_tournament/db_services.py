from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions import NotFoundError
from src.core.models import BaseServiceDB, TeamDB, TeamTournamentDB
from src.core.models.base import Database
from src.logging_config import get_logger
from src.team_tournament.schemas import TeamTournamentSchemaCreate

ITEM = "TEAM_TOURNAMENT"


class TeamTournamentServiceDB(BaseServiceDB):
    def __init__(self, database: Database) -> None:
        super().__init__(database, TeamTournamentDB)
        self.logger = get_logger("backend_logger_TeamTournamentServiceDB", self)
        self.logger.debug("Initialized TeamTournamentServiceDB")

    async def create(
        self,
        item: TeamTournamentSchemaCreate,
    ) -> TeamTournamentDB:
        self.logger.debug(f"Creat {ITEM} relation:{item}")
        is_relation_exist = await self.get_team_tournament_relation(
            item.team_id,
            item.tournament_id,
        )
        if is_relation_exist:
            return is_relation_exist
        return await super().create(item)

    async def get_team_tournament_relation(
        self, team_id: int, tournament_id: int
    ) -> TeamTournamentDB | None:
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
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(f"Database error on get_team_tournament_relation {ex}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Database error fetching team tournament relation",
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(f"Data error on get_team_tournament_relation: {ex}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail="Invalid data for team tournament relation",
            )
        except NotFoundError as ex:
            self.logger.info(f"Not found on get_team_tournament_relation: {ex}", exc_info=True)
            return None
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error on get_team_tournament_relation: {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error fetching team tournament relation",
            )

    async def get_related_teams(self, tournament_id: int) -> list[TeamDB]:
        try:
            self.logger.debug(f"Get {ITEM} related teams for tournament_id:{tournament_id}")
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
                f"Database error on get_related_teams: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error fetching related teams for tournament {tournament_id}",
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(
                f"Data error on get_related_teams: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid data for related teams",
            )
        except NotFoundError as ex:
            self.logger.info(
                f"Not found on get_related_teams: {ex}",
                exc_info=True,
            )
            return []
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error on get_related_teams: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error fetching related teams for tournament {tournament_id}",
            )

    async def delete_relation_by_team_and_tournament_id(
        self, team_id: int, tournament_id: int
    ) -> TeamTournamentDB:
        try:
            self.logger.debug(f"Delete {ITEM} team_id:{team_id} tournament_id:{tournament_id}")
            async with self.db.async_session() as session:
                result = await session.execute(
                    select(TeamTournamentDB).where(
                        (TeamTournamentDB.team_id == team_id)
                        & (TeamTournamentDB.tournament_id == tournament_id)
                    )
                )
                item = result.scalars().first()

                if not item:
                    raise NotFoundError(
                        f"Team tournament relation not found for team_id:{team_id} tournament_id:{tournament_id}"
                    )

                await session.delete(item)
                await session.commit()
                return item
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Database error on delete_relation_by_team_and_tournament_id: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Database error deleting team tournament relation",
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(
                f"Data error on delete_relation_by_team_and_tournament_id: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid data for team tournament relation",
            )
        except NotFoundError as ex:
            self.logger.info(
                f"Not found on delete_relation_by_team_and_tournament_id: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=404,
                detail="Resource not found",
            )
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error on delete_relation_by_team_and_tournament_id: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error deleting team tournament relation",
            )
