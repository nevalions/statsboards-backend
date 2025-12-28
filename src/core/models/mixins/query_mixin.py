from fastapi import HTTPException
from sqlalchemy import Column, Result, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class QueryMixin:
    async def get_item_by_field_value(self, value, field_name: str):
        self.logger.debug(
            f"Starting to fetch item by field {field_name} with value: {value} for model {self.model.__name__}"
        )
        async with self.db.async_session() as session:
            try:
                column: Column = getattr(self.model, field_name)
                self.logger.debug(
                    f"Accessed column: {column} for model {self.model.__name__}"
                )

                stmt = select(self.model).where(column == value)
                self.logger.debug(
                    f"Executing SQL statement: {stmt} for model {self.model.__name__}"
                )

                result: Result = await session.execute(stmt)
                self.logger.debug(
                    f"Query result: {result} for model {self.model.__name__}"
                )

                return result.scalars().one_or_none()
            except Exception as ex:
                self.logger.error(
                    f"Error fetching item by {field_name} with value {value}: {ex} for model {self.model.__name__}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch item for model {self.model.__name__}. Please try again later.",
                )

    async def update_item_by_eesl_id(
        self,
        eesl_field_name: str,
        eesl_value: int,
        new_item,
    ):
        async with self.db.async_session() as session:
            self.logger.info(
                f"Starting update_item_by_eesl_id with eesl_field_name: {eesl_field_name}, eesl_value: {eesl_value} for model {self.model.__name__}"
            )
            is_exist = await self.get_item_by_field_value(
                eesl_value,
                eesl_field_name,
            )
            if is_exist:
                self.logger.debug(
                    f"Item found with id: {is_exist.id} for model {self.model.__name__}"
                )
                update_dict = {}
                for key, value in new_item.__dict__.items():
                    if not key.startswith("_"):
                        update_dict[key] = value
                await session.execute(
                    update(self.model)
                    .where(getattr(self.model, eesl_field_name) == eesl_value)
                    .values(update_dict)
                )
                self.logger.debug(
                    f"Update operation executed for item with id: {is_exist.id} for model {self.model.__name__}"
                )
                await session.commit()
                find_updated = await self.get_by_id(is_exist.id)
                self.logger.debug(
                    f"Updated item retrieved with id: {find_updated.id} for model {self.model.__name__}"
                )
                return find_updated
            else:
                self.logger.error(f"No item found for model {self.model.__name__}")
                return None

    async def get_count_of_items_level_one_by_id(
        self,
        item_id: int,
        related_property: str,
    ):
        async with self.db.async_session() as session:
            self.logger.debug(
                f"Getting item first with id {item_id} and property {related_property}"
            )

            query = select(self.model).where(self.model.id == item_id)
            item_result = await session.execute(query)
            item = item_result.scalars().one_or_none()

            if not item:
                return 0
            try:
                self.logger.debug(
                    f"Fetching count of related items for {item_id} and property {related_property}"
                )

                if not hasattr(self.model, related_property):
                    self.logger.error(
                        f"Invalid relationship: {related_property} does not exist"
                    )
                    return 0

                relationship = getattr(self.model, related_property)

                if not hasattr(relationship.property, "mapper"):
                    self.logger.error(f"{related_property} is not a valid relationship")
                    return 0

                related_model = relationship.property.mapper.class_

                foreign_keys = [
                    col
                    for col in related_model.__table__.columns
                    if col.foreign_keys
                    and self.model.__tablename__
                    in [fk.column.table.name for fk in col.foreign_keys]
                ]

                if not foreign_keys:
                    self.logger.error(
                        f"No valid foreign key found for relationship {related_property}"
                    )
                    return 0

                foreign_key_column = foreign_keys[0]

                self.logger.debug(f"Foreign Key Column: {foreign_key_column.name}")

                from sqlalchemy.sql import func

                query_count = select(func.count()).where(
                    getattr(related_model, foreign_key_column.name) == item_id
                )

                self.logger.debug(f"Generated Query: {query_count}")

                result = await session.execute(query_count)
                return result.scalar() or 0

            except Exception:
                return 0
