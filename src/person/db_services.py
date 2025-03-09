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
        try:
            self.logger.debug(f"Creat or update {ITEM}:{p}")
            if p.person_eesl_id:
                person_from_db = await self.get_person_by_eesl_id(p.person_eesl_id)
                if person_from_db:
                    self.logger.debug(
                        f"{ITEM} eesl_id:{p.person_eesl_id} already exists updating"
                    )
                    self.logger.debug(f"Get {ITEM} eesl_id:{p.person_eesl_id}")
                    return await self.update_person_by_eesl(
                        "person_eesl_id",
                        p,
                    )
                else:
                    return await self.create_new_person(
                        p,
                    )
            else:
                return await self.create_new_person(
                    p,
                )
        except Exception as ex:
            self.logger.error(f"{ITEM} {p} returned an error: {ex}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"{ITEM} ({p}) returned some error",
            )

    async def update_person_by_eesl(
        self,
        eesl_field_name: str,
        p: PersonSchemaUpdate,
    ):
        self.logger.debug(f"Update {ITEM} {eesl_field_name}:{p.person_eesl_id}")
        return await self.update_item_by_eesl_id(
            eesl_field_name,
            p.person_eesl_id,
            p,
        )

    async def create_new_person(
        self,
        p: PersonSchemaCreate,
    ):
        person = self.model(
            first_name=p.first_name,
            second_name=p.second_name,
            person_photo_url=p.person_photo_url,
            person_photo_icon_url=p.person_photo_icon_url,
            person_photo_web_url=p.person_photo_web_url,
            person_dob=p.person_dob,
            person_eesl_id=p.person_eesl_id,
        )
        self.logger.debug(f"Create new {ITEM}:{p}")
        return await super().create(person)

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
