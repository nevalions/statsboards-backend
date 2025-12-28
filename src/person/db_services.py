from fastapi import HTTPException

from src.core.models import BaseServiceDB, PersonDB

from ..logging_config import get_logger, setup_logging
from .schemas import PersonSchemaCreate, PersonSchemaUpdate

setup_logging()
ITEM = "PERSON"


class PersonServiceDB(BaseServiceDB):
    def __init__(
        self,
        database,
    ):
        super().__init__(database, PersonDB)
        self.logger = get_logger("backend_logger_PersonServiceDB", self)
        self.logger.debug("Initialized PersonServiceDB")

    async def create_or_update_person(
        self,
        p: PersonSchemaCreate | PersonSchemaUpdate,
    ):
        return await super().create_or_update(p, eesl_field_name="person_eesl_id")

    async def get_person_by_eesl_id(
        self,
        value,
        field_name="person_eesl_id",
    ):
        self.logger.debug(f"Get {ITEM} {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def update_person(
        self,
        item_id: int,
        item: PersonSchemaUpdate,
        **kwargs,
    ):
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
