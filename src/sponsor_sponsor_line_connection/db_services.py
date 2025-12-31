from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions import NotFoundError
from src.core.models import (
    BaseServiceDB,
    SponsorDB,
    SponsorLineDB,
    SponsorSponsorLineDB,
)
from src.core.models.base import Database

from ..logging_config import get_logger
from .schemas import SponsorSponsorLineSchemaCreate
ITEM = "SPONSOR_SPONSOR_LINE"


class SponsorSponsorLineServiceDB(BaseServiceDB):
    def __init__(self, database: Database) -> None:
        super().__init__(database, SponsorSponsorLineDB)
        self.logger = get_logger("backend_logger_SponsorSponsorLineServiceDB", self)
        self.logger.debug("Initialized SponsorSponsorLineServiceDB")

    async def create(
        self,
        item: SponsorSponsorLineSchemaCreate,
    ) -> SponsorSponsorLineDB | None:
        try:
            self.logger.debug(f"Creating {ITEM}")
            is_relation_exist = await self.get_sponsor_sponsor_line_relation(
                item.sponsor_line_id,
                item.sponsor_id,
            )
            if is_relation_exist:
                self.logger.debug(f"Relation {ITEM} already exists")
                return None
            new_sponsor_sponsor_line = self.model(
                sponsor_line_id=item.sponsor_line_id,
                sponsor_id=item.sponsor_id,
                position=item.position,
            )
            return await super().create(new_sponsor_sponsor_line)
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as e:
            self.logger.error(f"Database error creating {ITEM}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Database error creating {ITEM}",
            )
        except (ValueError, KeyError, TypeError) as e:
            self.logger.warning(f"Data error creating {ITEM}: {e}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data provided for {ITEM}",
            )
        except NotFoundError as e:
            self.logger.info(f"Not found creating {ITEM}: {e}", exc_info=True)
            return None
        except Exception as e:
            self.logger.critical(f"Unexpected error creating {ITEM}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error creating {ITEM}",
            )

    async def get_sponsor_sponsor_line_relation(
        self, sponsor_id: int, sponsor_line_id: int
    ) -> SponsorSponsorLineDB | None:
        async with self.db.async_session() as session:
            try:
                self.logger.debug(f"Getting {ITEM}")
                result = await session.execute(
                    select(SponsorSponsorLineDB).where(
                        (SponsorSponsorLineDB.sponsor_id == sponsor_id)
                        & (SponsorSponsorLineDB.sponsor_line_id == sponsor_line_id)
                    )
                )
                sponsor_sponsor_line = result.scalars().first()
                await session.commit()
                return sponsor_sponsor_line
            except HTTPException:
                raise
            except (IntegrityError, SQLAlchemyError) as e:
                self.logger.error(f"Database error getting {ITEM}: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error fetching {ITEM}",
                )
            except (ValueError, KeyError, TypeError) as e:
                self.logger.warning(f"Data error getting {ITEM}: {e}", exc_info=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid data provided for {ITEM}",
                )
            except NotFoundError as e:
                self.logger.info(f"Not found getting {ITEM}: {e}", exc_info=True)
                return None
            except Exception as e:
                self.logger.critical(f"Unexpected error getting {ITEM}: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error fetching {ITEM}",
                )

    async def get_related_sponsors(self, sponsor_line_id: int) -> dict:
        async with self.db.async_session() as session:
            try:
                self.logger.debug(
                    f"Getting sponsors by sponsor line id: {sponsor_line_id}"
                )
                sponsor_line = await session.get(SponsorLineDB, sponsor_line_id)
                result = await session.execute(
                    select(SponsorDB, SponsorSponsorLineDB.position)
                    .join(
                        SponsorSponsorLineDB,
                        SponsorDB.id == SponsorSponsorLineDB.sponsor_id,
                    )
                    .where(SponsorSponsorLineDB.sponsor_line_id == sponsor_line_id)
                )
                sponsors = [{"sponsor": r[0], "position": r[1]} for r in result.all()]
                await session.commit()
                return {"sponsor_line": sponsor_line, "sponsors": sponsors}
            except HTTPException:
                raise
            except (IntegrityError, SQLAlchemyError) as e:
                self.logger.error(
                    f"Database error getting related sponsors by sponsor line id:{sponsor_line_id}: {e}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error fetching sponsors by sponsor line {sponsor_line_id}",
                )
            except (ValueError, KeyError, TypeError) as e:
                self.logger.warning(
                    f"Data error getting related sponsors by sponsor line id:{sponsor_line_id}: {e}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid data provided for sponsor sponsors",
                )
            except NotFoundError as e:
                self.logger.info(
                    f"Not found getting related sponsors by sponsor line id:{sponsor_line_id}: {e}",
                    exc_info=True,
                )
                return {"sponsor_line": None, "sponsors": []}
            except Exception as e:
                self.logger.critical(
                    f"Unexpected error getting related sponsors by sponsor line id:{sponsor_line_id}: {e}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error fetching sponsors by sponsor line {sponsor_line_id}",
                )

    async def delete_relation_by_sponsor_and_sponsor_line_id(
        self, sponsor_id: int, sponsor_line_id: int
    ) -> SponsorSponsorLineDB:
        async with self.db.async_session() as session:
            try:
                self.logger.debug(f"Deleting {ITEM}")
                result = await session.execute(
                    select(SponsorSponsorLineDB).where(
                        (SponsorSponsorLineDB.sponsor_id == sponsor_id)
                        & (SponsorSponsorLineDB.sponsor_line_id == sponsor_line_id)
                    )
                )

                item = result.scalars().first()

                if not item:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Connection sponsor id: {sponsor_id} and sponsor_line id {sponsor_line_id} not found",
                    )

                await session.delete(item)
                await session.commit()
                self.logger.info(
                    f"Deleted {ITEM}: sponsor_id={sponsor_id}, sponsor_line_id={sponsor_line_id}"
                )
                return item
            except HTTPException:
                raise
            except (IntegrityError, SQLAlchemyError) as e:
                self.logger.error(f"Database error deleting {ITEM}: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error deleting {ITEM}",
                )
            except (ValueError, KeyError, TypeError) as e:
                self.logger.warning(f"Data error deleting {ITEM}: {e}", exc_info=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid data provided for {ITEM}",
                )
            except NotFoundError as e:
                self.logger.info(f"Not found deleting {ITEM}: {e}", exc_info=True)
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                self.logger.critical(f"Unexpected error deleting {ITEM}: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error deleting {ITEM}",
                )
