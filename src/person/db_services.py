from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions import NotFoundError
from src.core.models import BaseServiceDB, PersonDB
from src.core.models.base import Database

from ..logging_config import get_logger
from .schemas import PersonSchemaCreate, PersonSchemaUpdate
ITEM = "PERSON"


class PersonServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, PersonDB)
        self.logger = get_logger("backend_logger_PersonServiceDB", self)
        self.logger.debug("Initialized PersonServiceDB")

    async def create(
        self,
        item: PersonSchemaCreate | PersonSchemaUpdate,
    ) -> PersonDB:
        try:
            person = self.model(
                person_eesl_id=item.person_eesl_id,
                first_name=item.first_name,
                second_name=item.second_name,
                person_photo_url=item.person_photo_url,
                person_photo_icon_url=item.person_photo_icon_url,
                person_photo_web_url=item.person_photo_web_url,
                person_dob=item.person_dob,
            )
            self.logger.debug(
                f"Starting to create PersonDB with data: {person.__dict__}"
            )
            return await super().create(person)
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(f"Database error creating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Database error creating {self.model.__name__}",
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(f"Data error creating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided",
            )
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error in {self.__class__.__name__}.create: {ex}",
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
            )

    async def create_or_update_person(
        self,
        p: PersonSchemaCreate | PersonSchemaUpdate,
    ) -> PersonDB | None:
        return await super().create_or_update(p, eesl_field_name="person_eesl_id")

    async def get_person_by_eesl_id(
        self,
        value: int | str,
        field_name: str = "person_eesl_id",
    ) -> PersonDB | None:
        self.logger.debug(f"Get {ITEM} {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def update(
        self,
        item_id: int,
        item: PersonSchemaUpdate,
        **kwargs,
    ) -> PersonDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
