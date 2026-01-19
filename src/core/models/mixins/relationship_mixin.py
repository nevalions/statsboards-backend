from typing import TYPE_CHECKING, Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundError

if TYPE_CHECKING:
    from logging import LoggerAdapter

    from src.core.models.base import Base, Database


class RelationshipMixin:
    db: "Database"
    logger: "LoggerAdapter"
    model: type["Base"]

    async def find_relation(
        self,
        secondary_table,
        fk_item_one: int,
        fk_item_two: int,
        field_name_one: str,
        field_name_two: str,
    ):
        async with self.db.async_session() as session:
            self.logger.debug(f"Starting find_relation for model {self.model.__name__}")
            existing_relation = await session.execute(
                select(secondary_table).filter(
                    (getattr(secondary_table, field_name_one) == fk_item_one)
                    & (getattr(secondary_table, field_name_two) == fk_item_two)
                )
            )
            result = existing_relation.scalar()
            if result:
                self.logger.debug(
                    f"Relation found {existing_relation.__dict__} for model {self.model.__name__}"
                )
            else:
                self.logger.debug(f"No relation found for model {self.model.__name__}")
            return result

    async def is_relation_exist(
        self,
        secondary_table,
        fk_item_one: int,
        fk_item_two: int,
        field_name_one: str,
        field_name_two: str,
    ) -> bool:
        existing_record = await self.find_relation(
            secondary_table,
            fk_item_one,
            fk_item_two,
            field_name_one,
            field_name_two,
        )
        if existing_record:
            return True
        else:
            self.logger.debug(f"No relation found for model {self.model.__name__}")
            return False

    async def create_m2m_relation(
        self,
        parent_model,
        child_model,
        secondary_table,
        parent_id: int,
        child_id: int,
        parent_id_name: str,
        child_id_name: str,
        child_relation,
    ):
        async with self.db.async_session() as session:
            existing_relation = await self.is_relation_exist(
                secondary_table,
                parent_id,
                child_id,
                parent_id_name,
                child_id_name,
            )

            if existing_relation:
                self.logger.warning(
                    f"Parent {parent_model.__name__}-{child_model.__name__} relation already exists for model {self.model.__name__}"
                )
                raise HTTPException(
                    status_code=409,
                    detail=f"{parent_model.__name__}-{child_model.__name__} relation "
                    f"already exists for model {self.model.__name__}",
                )

            parent = await session.scalar(
                select(parent_model)
                .where(parent_model.id == parent_id)
                .options(selectinload(getattr(parent_model, child_relation))),
            )
            if parent:
                self.logger.debug(
                    f"Parent {parent_model.__name__} found with id: {parent_id} for model {self.model.__name__}"
                )
                child = await session.execute(select(child_model).where(child_model.id == child_id))
                child_new = child.scalar()
                if child_new:
                    self.logger.debug(
                        f"Child {child_model.__name__} found with id: {child_id} for model {self.model.__name__}"
                    )
                    try:
                        getattr(parent, child_relation).append(child_new)
                        await session.commit()
                        self.logger.info(
                            f"Relation created between {parent_model.__name__} and {child_model.__name__} for model {self.model.__name__}"
                        )
                        return list(getattr(parent, child_relation))
                    except HTTPException:
                        await session.rollback()
                        raise
                    except (IntegrityError, SQLAlchemyError) as ex:
                        self.logger.error(
                            f"Database error creating relation between {parent_model.__name__} and {child_model.__name__}: {ex} for model {self.model.__name__}",
                            exc_info=True,
                        )
                        await session.rollback()
                        return None
                    except (ValueError, KeyError, TypeError) as ex:
                        self.logger.warning(
                            f"Data error creating relation between {parent_model.__name__} and {child_model.__name__}: {ex} for model {self.model.__name__}",
                            exc_info=True,
                        )
                        await session.rollback()
                        return None
                    except Exception as ex:
                        self.logger.critical(
                            f"Unexpected error in {self.__class__.__name__}.create_m2m_relation: {ex}",
                            exc_info=True,
                        )
                        await session.rollback()
                        return None
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"{child_model.__name__} id:{child_id} for model {self.model.__name__} not found",
                    )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"{parent_model.__name__} id:{parent_id} for model {self.model.__name__} not found",
                )

    async def get_related_items(
        self,
        item_id: int,
        related_property: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ):
        async with self.db.async_session() as session:
            self.logger.debug(
                f"Fetching related items for id: {item_id} and property: {related_property} for model {self.model.__name__}"
            )
            try:
                query = (
                    select(self.model)
                    .where(self.model.id == item_id)
                    .options(selectinload(getattr(self.model, related_property)))
                    if related_property
                    else select(self.model).where(self.model.id == item_id)
                )

                item = await session.execute(query)
                result = item.scalars().one()

                if result:
                    self.logger.debug(
                        f"Item found with related items for property: {related_property} for model {self.model.__name__}"
                    )
                    return result
                else:
                    self.logger.warning(
                        f"No result found for id: {item_id} for model {self.model.__name__}"
                    )
                    return None

            except NoResultFound:
                self.logger.warning(
                    f"No result found for id: {item_id} for model {self.model.__name__}"
                )
                return None

    async def get_related_item_level_one_by_id(
        self,
        item_id: int,
        related_property: str,
        skip: int | None = None,
        limit: int | None = None,
        order_by: str = "id",
        order_by_two: str = "id",
        ascending: bool = True,
    ):
        async with self.db.async_session() as session:
            try:
                self.logger.debug(
                    f"Fetching related items for item id one level: {item_id} and property: {related_property} "
                    f"for model {self.model.__name__}"
                )

                query = select(self.model).where(self.model.id == item_id)

                item_result = await session.execute(query)
                item = item_result.scalars().one_or_none()

                if skip is not None and limit is not None:
                    relationship = getattr(self.model, related_property)
                    related_model = relationship.property.mapper.class_

                    try:
                        order_column = getattr(related_model, order_by)
                    except AttributeError:
                        self.logger.warning(f"Order column {order_by} not found, defaulting to id")
                        order_column = related_model.id

                    try:
                        order_column_two = getattr(related_model, order_by_two)
                    except AttributeError:
                        self.logger.warning(
                            f"Order column {order_by_two} not found, defaulting to id"
                        )
                        order_column_two = related_model.id

                    order_expr = order_column.asc() if ascending else order_column.desc()
                    order_expr_two = (
                        order_column_two.asc() if ascending else order_column_two.desc()
                    )

                    query = (
                        select(related_model)
                        .join(getattr(self.model, related_property))
                        .where(self.model.id == item_id)
                        .order_by(order_expr, order_expr_two)
                        .offset(skip)
                        .limit(limit)
                    )

                    result = await session.execute(query)
                    related_items = result.scalars().all()

                    if related_items:
                        self.logger.debug(
                            f"Related items found for property: {related_property} for model {self.model.__name__}"
                        )
                    else:
                        self.logger.debug(
                            f"No related item found one level for property: {related_property} "
                            f"for model {self.model.__name__}"
                        )
                    return list(related_items)
                else:
                    query = (
                        select(self.model)
                        .where(self.model.id == item_id)
                        .options(selectinload(getattr(self.model, related_property)))
                    )

                    item = await session.execute(query)
                    all_related_items = getattr(item.scalars().one(), related_property)

                    if all_related_items:
                        item_count = (
                            len(all_related_items) if hasattr(all_related_items, "__len__") else 1
                        )
                        self.logger.debug(
                            f"Related items ({item_count}) found for property: {related_property} "
                            f"for model {self.model.__name__}"
                        )
                    else:
                        self.logger.debug(
                            f"No related item found one level for property: {related_property} "
                            f"for model {self.model.__name__}"
                        )
                    return all_related_items

            except NoResultFound:
                self.logger.warning(
                    f"No result found for item id one level: {item_id} and property: {related_property} "
                    f"for model {self.model.__name__}"
                )
                return None

    async def get_nested_related_item_by_id(
        self,
        item_id: int,
        service: Any,
        related_property: str,
        nested_related_property: str,
    ):
        related_item = await self.get_related_item_level_one_by_id(item_id, related_property)

        if related_item is not None:
            if hasattr(related_item, "id") and related_item.id:  # type: ignore[attr-defined]
                _id = related_item.id  # type: ignore[attr-defined]
                self.logger.debug(
                    f"Fetching nested related items for item id: {_id} and property: {related_property} "
                    f"and nested_related_property {nested_related_property} for model {self.model.__name__}"
                )
                item = await service.get_related_item_level_one_by_id(_id, nested_related_property)
                self.logger.debug(
                    f"Related item {item} found for item id: {_id} "
                    f"and nested_related_property: {nested_related_property} for model {self.model.__name__}"
                )
                return item
        self.logger.warning(
            f"No result found for item id: {item_id} and property: {related_property} "
            f"and nested_related_property {nested_related_property} for model {self.model.__name__}"
        )
        return None

    async def get_related_item_level_one_by_key_and_value(
        self,
        filter_key: str,
        filter_value: Any,
        related_property: str,
    ):
        async with self.db.async_session() as session:
            try:
                self.logger.debug(
                    f"Fetching related items for key: {filter_key} and value: {filter_value} for model {self.model.__name__}"
                )
                item = await session.execute(
                    select(self.model)
                    .where(getattr(self.model, filter_key) == filter_value)
                    .options(selectinload(getattr(self.model, related_property)))
                )
                result = getattr(item.scalars().one(), related_property)
                if result:
                    self.logger.debug(
                        f"Related item found {result} for property: {related_property} for model {self.model.__name__}"
                    )
                else:
                    self.logger.debug(
                        f"No related item found for property: {related_property} for model {self.model.__name__}"
                    )
                return result
            except NoResultFound:
                self.logger.warning(
                    f"No result found for key: {filter_key} and value: {filter_value} for model {self.model.__name__}"
                )
                return None

    async def get_related_items_by_two(
        self,
        filter_key: str,
        filter_value: Any,
        second_model,
        related_property: str,
        second_level_property: str,
    ):
        async with self.db.async_session() as session:
            try:
                self.logger.debug(
                    f"Fetching related item by two level for "
                    f"key: {filter_key} and value: {filter_value} for model {self.model.__name__}"
                )
                query = (
                    select(self.model)
                    .where(getattr(self.model, filter_key) == filter_value)
                    .options(
                        selectinload(getattr(self.model, related_property)).joinedload(
                            getattr(second_model, second_level_property)
                        )
                    )
                )

                result = await session.execute(query)
                item = result.unique().scalars().one_or_none()

                if item:
                    self.logger.debug(
                        f"Item {item} found for "
                        f"key: {filter_key} and value: {filter_value} for model {self.model.__name__}"
                    )
                    related_items = getattr(item, related_property)
                    items = []
                    for related_item in related_items:
                        second_level = getattr(related_item, second_level_property)
                        if hasattr(second_level, "__iter__") and not isinstance(
                            second_level, (str, bytes)
                        ):
                            for final_point in second_level:
                                items.append(final_point)
                        else:
                            items.append(second_level)
                    return items
                else:
                    self.logger.warning(
                        f"No item found for "
                        f"ey: {filter_key} and value: {filter_value} for model {self.model.__name__}"
                    )
                    raise HTTPException(
                        status_code=404,
                        detail=f"{second_model} {filter_key} not found for model {self.model.__name__}",
                    )
            except HTTPException:
                raise
            except (IntegrityError, SQLAlchemyError) as e:
                self.logger.error(
                    f"Database error fetching related item for key: {filter_key} and value {filter_value} "
                    f"for model {self.model.__name__}: {e}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error fetching {self.model.__name__}",
                )
            except (ValueError, KeyError, TypeError) as e:
                self.logger.warning(
                    f"Data error fetching related item for key: {filter_key} and value {filter_value} "
                    f"for model {self.model.__name__}: {e}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=400,
                    detail="Invalid data provided",
                )
            except NotFoundError as e:
                self.logger.info(
                    f"Resource not found for key: {filter_key} and value {filter_value}: {e} for model {self.model.__name__}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=404,
                    detail="Database error",
                )
            except Exception as e:
                self.logger.critical(
                    f"Unexpected error in {self.__class__.__name__}.get_related_items_by_two({filter_key}, {filter_value}): {e}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error",
                )
