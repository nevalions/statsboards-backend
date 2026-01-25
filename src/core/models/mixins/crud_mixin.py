import asyncio
import logging
from typing import TYPE_CHECKING

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from src.core.models.base import Base, Database


class CRUDMixin:
    if TYPE_CHECKING:
        logger: logging.LoggerAdapter
        model: type["Base"]
        db: "Database"

    async def create(self, item):
        max_retries = 2 if hasattr(self.db, "test_mode") and self.db.test_mode else 0
        attempt = 0

        while True:
            async with self.db.async_session() as session:
                self.logger.debug(
                    f"Starting to create {self.model.__name__} with data: {item.__dict__}"
                )
                try:
                    if isinstance(item, BaseModel):
                        item_to_add = self.model(**item.model_dump())
                    elif attempt > 0:
                        item_to_add = self.model(
                            **{
                                key: value
                                for key, value in item.__dict__.items()
                                if not key.startswith("_sa_")
                            }
                        )
                    else:
                        item_to_add = item

                    session.add(item_to_add)
                    if hasattr(self.db, "test_mode") and self.db.test_mode:
                        await session.flush()
                    else:
                        await session.commit()
                    await session.refresh(item_to_add)
                    self.logger.info(
                        f"{self.model.__name__} created successfully: {item_to_add.__dict__}"
                    )
                    return item_to_add
                except IntegrityError as ex:
                    self.logger.error(
                        f"Integrity error creating {self.model.__name__}: {ex}",
                        exc_info=True,
                    )
                    await session.rollback()
                    raise
                except SQLAlchemyError as ex:
                    await session.rollback()
                    if (
                        attempt < max_retries
                        and "deadlock detected" in str(ex).lower()
                        and hasattr(self.db, "test_mode")
                        and self.db.test_mode
                    ):
                        attempt += 1
                        await asyncio.sleep(0.05 * attempt)
                        continue
                    raise
                except Exception:
                    await session.rollback()
                    raise

    async def get_all_elements(self):
        async with self.db.async_session() as session:
            stmt = select(self.model)

            items = await session.execute(stmt)
            result = items.scalars().all()
            self.logger.debug(f"Fetched list of {len(result)} elements for {self.model.__name__}")
            return list(result)

    async def get_by_id(self, item_id: int):
        self.logger.debug(f"Starting to fetch element with ID: {item_id} for {self.model.__name__}")
        try:
            async with self.db.async_session() as session:
                result = await session.execute(select(self.model).where(self.model.id == item_id))
                if result:
                    final_result = result.scalars().one_or_none()
                    if final_result:
                        self.logger.debug(f"Result found: {final_result.__dict__}")
                        self.logger.debug(
                            f"Fetched element successfully with ID:{item_id} for {self.model.__name__}"
                        )
                        return final_result
                    else:
                        self.logger.warning(f"No element with ID:{item_id} found")
                        return None

                else:
                    self.logger.warning(
                        f"No element found with ID: {item_id} for {self.model.__name__}"
                    )
                    return None
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Database error fetching element with ID: {item_id} for {self.model.__name__}: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error fetching {self.model.__name__}",
            ) from ex
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(
                f"Data error fetching element with ID: {item_id} for {self.model.__name__}: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided",
            ) from ex
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error in {self.__class__.__name__}.get_by_id({item_id}): {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
            ) from ex

    async def get_by_id_and_model(
        self,
        model,
        item_id: int,
    ):
        self.logger.debug(f"Starting to fetch element with ID: {item_id} for {model.__name__}")
        try:
            async with self.db.async_session() as session:
                result = await session.execute(select(model).where(model.id == item_id))
                item = result.scalars().one_or_none()
                if item is not None:
                    self.logger.debug(
                        f"Fetched element with ID {item_id} for {model.__name__}: {item.__dict__}"
                    )
                else:
                    self.logger.warning(f"No element found with ID: {item_id} for {model.__name__}")
                return item
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Database error fetching element with ID: {item_id} for {model.__name__}: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error fetching {model.__name__}",
            ) from ex
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(
                f"Data error fetching element with ID: {item_id} for {model.__name__}: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided",
            ) from ex
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error in {self.__class__.__name__}.get_by_id_and_model({item_id}): {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
            ) from ex

    async def update(self, item_id: int, item, **kwargs):
        self.logger.debug(f"Starting to update element with ID: {item_id}")
        async with self.db.async_session() as session:
            try:
                result = await session.execute(select(self.model).where(self.model.id == item_id))
                updated_item = result.scalars().one_or_none()

                if not updated_item:
                    self.logger.warning(
                        f"No element found with ID: {item_id} for model {self.model.__name__}"
                    )
                    return None

                update_data = item.model_dump(exclude_unset=True, exclude_none=True)

                for key, value in update_data.items():
                    setattr(updated_item, key, value)

                await session.flush()
                await session.commit()
                await session.refresh(updated_item)

                self.logger.debug(f"Updated element with ID: {item_id}: {updated_item.__dict__}")
                return updated_item
            except HTTPException:
                await session.rollback()
                raise
            except (IntegrityError, SQLAlchemyError) as ex:
                self.logger.error(
                    f"Database error updating element with ID: {item_id} for {self.model.__name__}: {ex}",
                    exc_info=True,
                )
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error updating {self.model.__name__}",
                ) from ex
            except (ValueError, KeyError, TypeError) as ex:
                self.logger.warning(
                    f"Data error updating element with ID: {item_id} for {self.model.__name__}: {ex}",
                    exc_info=True,
                )
                await session.rollback()
                raise HTTPException(
                    status_code=400,
                    detail="Invalid data provided",
                ) from ex
            except Exception as ex:
                self.logger.critical(
                    f"Unexpected error in {self.__class__.__name__}.update({item_id}): {ex}",
                    exc_info=True,
                )
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error",
                ) from ex

    async def delete(self, item_id: int):
        self.logger.debug(f"Starting to delete element with ID: {item_id}")
        async with self.db.async_session() as session:
            try:
                db_item = await self.get_by_id(item_id)
                if not db_item:
                    raise HTTPException(
                        status_code=404,
                        detail=f"{self.model.__name__} not found",
                    )
                await session.delete(db_item)
                await session.commit()
                self.logger.info(f"Deleted element with ID: {item_id}: {db_item.__dict__}")
                return {"id": item_id}
            except HTTPException:
                await session.rollback()
                raise
            except (IntegrityError, SQLAlchemyError) as ex:
                self.logger.error(
                    f"Database error deleting element with ID: {item_id} for {self.model.__name__}: {ex}",
                    exc_info=True,
                )
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error deleting {self.model.__name__}",
                ) from ex
            except (ValueError, KeyError, TypeError) as ex:
                self.logger.warning(
                    f"Data error deleting element with ID: {item_id} for {self.model.__name__}: {ex}",
                    exc_info=True,
                )
                await session.rollback()
                raise HTTPException(
                    status_code=400,
                    detail="Invalid data provided",
                ) from ex
            except Exception as ex:
                self.logger.critical(
                    f"Unexpected error in {self.__class__.__name__}.delete({item_id}): {ex}",
                    exc_info=True,
                )
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error",
                ) from ex

    async def get_count(self) -> int:
        self.logger.debug(f"Getting count of {self.model.__name__} elements")
        try:
            async with self.db.async_session() as session:
                stmt = select(func.count()).select_from(self.model)
                result = await session.execute(stmt)
                count = result.scalar()
                self.logger.debug(f"Count of {self.model.__name__}: {count}")
                return count or 0
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Database error getting count of {self.model.__name__}: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error counting {self.model.__name__}",
            ) from ex
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error in {self.__class__.__name__}.get_count(): {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
            ) from ex

    async def get_all_with_pagination(
        self,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "id",
        order_by_two: str = "id",
        ascending: bool = True,
    ):
        self.logger.debug(
            f"Getting paginated {self.model.__name__} elements: skip={skip}, limit={limit}, "
            f"order_by={order_by}, order_by_two={order_by_two}, ascending={ascending}"
        )
        try:
            async with self.db.async_session() as session:
                try:
                    order_column = getattr(self.model, order_by, self.model.id)
                except AttributeError:
                    self.logger.warning(
                        f"Order column {order_by} not found for {self.model.__name__}, defaulting to id"
                    )
                    order_column = self.model.id

                try:
                    order_column_two = getattr(self.model, order_by_two, self.model.id)
                except AttributeError:
                    self.logger.warning(
                        f"Order column {order_by_two} not found for {self.model.__name__}, defaulting to id"
                    )
                    order_column_two = self.model.id

                order_expr = order_column.asc() if ascending else order_column.desc()
                order_expr_two = order_column_two.asc() if ascending else order_column_two.desc()

                stmt = (
                    select(self.model)
                    .order_by(order_expr, order_expr_two)
                    .offset(skip)
                    .limit(limit)
                )

                result = await session.execute(stmt)
                items = result.scalars().all()
                self.logger.debug(
                    f"Fetched {len(items)} paginated elements for {self.model.__name__}"
                )
                return list(items)
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(
                f"Database error getting paginated {self.model.__name__}: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Database error fetching {self.model.__name__}",
            ) from ex
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error in {self.__class__.__name__}.get_all_with_pagination(): {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
            ) from ex
