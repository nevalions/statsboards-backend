from fastapi import HTTPException, UploadFile

from src.core.models import db, BaseServiceDB, PersonDB

from .schemas import PersonSchemaCreate, PersonSchemaUpdate


class PersonServiceDB(BaseServiceDB):
    def __init__(
            self,
            database,
    ):
        super().__init__(database, PersonDB)

    async def create_or_update_person(
            self,
            t: PersonSchemaCreate | PersonSchemaUpdate,
    ):
        try:
            if t.person_eesl_id:
                person_from_db = await self.get_person_by_eesl_id(t.person_eesl_id)
                if person_from_db:
                    return await self.update_person_by_eesl(
                        "person_eesl_id",
                        t,
                    )
                else:
                    return await self.create_new_person(
                        t,
                    )
            else:
                return await self.create_new_person(
                    t,
                )
        except Exception as ex:
            print(ex)
            raise HTTPException(
                status_code=409,
                detail=f"Person eesl " f"id({t}) " f"returned some error",
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

    # async def get_matches_by_person_id(
    #         self,
    #         person_id: int,
    # ):
    #     return await self.get_related_items_level_one_by_id(
    #         person_id,
    #         "matches",
    #     )

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

# async def get_person_db() -> PersonServiceDB:
#     yield PersonServiceDB(db)
#
#
# async def async_main() -> None:
#     person_service = PersonServiceDB(db)
#     # t = await person_service.get_person_by_id(1)
#     # t = await person_service.find_person_tournament_relation(6, 2)
#     # print(t)
#     t = await person_service.get_person_by_eesl_id(1)
#     if t:
#         print(t.__dict__)
#
#
# if __name__ == "__main__":
#     asyncio.run(async_main())
