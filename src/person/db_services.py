from fastapi import HTTPException

from src.core.models import BaseServiceDB, PersonDB
from .schemas import PersonSchemaCreate, PersonSchemaUpdate


class PersonServiceDB(BaseServiceDB):
    def __init__(
            self,
            database,
    ):
        super().__init__(database, PersonDB)

    async def create_or_update_person(
            self,
            p: PersonSchemaCreate | PersonSchemaUpdate,
    ):
        try:
            if p.person_eesl_id:
                person_from_db = await self.get_person_by_eesl_id(p.person_eesl_id)
                if person_from_db:
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
            print(ex)
            raise HTTPException(
                status_code=409,
                detail=f"Person eesl " f"id({p}) " f"returned some error",
            )

    async def update_person_by_eesl(
            self,
            eesl_field_name: str,
            p: PersonSchemaUpdate,
    ):
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

        print('person', person)
        return await super().create(person)

    async def get_person_by_eesl_id(
            self,
            value,
            field_name="person_eesl_id",
    ):
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
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
