from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions import NotFoundError
from src.core.models import BaseServiceDB, SponsorDB
from src.core.models.base import Database
from src.logging_config import get_logger, setup_logging
from src.sponsors.schemas import SponsorSchemaCreate, SponsorSchemaUpdate

setup_logging()
ITEM = "SPONSOR"


class SponsorServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, SponsorDB)
        self.logger = get_logger("backend_logger_SponsorServiceDB")
        self.logger.debug("Initialized SponsorServiceDB")

    async def create(
        self,
        item: SponsorSchemaCreate,
    ) -> SponsorDB:
        try:
            self.logger.debug(f"Creating {ITEM} {item}")
            sponsor = self.model(
                title=item.title,
                logo_url=item.logo_url,
                scale_logo=item.scale_logo,
            )

            result = await super().create(sponsor)
            if result is None:
                self.logger.warning(f"Failed to create {ITEM}")
                raise HTTPException(
                    status_code=409,
                    detail=f"Failed to create {self.model.__name__}. Check input data.",
                )
            return result
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as e:
            self.logger.error(f"Database error creating {ITEM}: {e}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"Database error creating {ITEM}",
            )
        except (ValueError, KeyError, TypeError) as e:
            self.logger.warning(f"Data error creating {ITEM}: {e}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided for sponsor",
            )
        except NotFoundError as e:
            self.logger.info(f"Not found creating {ITEM}: {e}", exc_info=True)
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            self.logger.critical(f"Unexpected error creating {ITEM}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Internal server error creating {ITEM}"
            )

    async def update(
        self,
        item_id: int,
        item: SponsorSchemaUpdate,
        **kwargs,
    ) -> SponsorDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
