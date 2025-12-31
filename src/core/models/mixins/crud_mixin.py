import logging
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions import NotFoundError

if TYPE_CHECKING:
    from src.core.models.base import Base, Database


class CRUDMixin:
    if TYPE_CHECKING:
        logger: logging.LoggerAdapter
        model: type["Base"]
        db: "Database"

    async def create(self, item):
        async with self.db.async_session() as session:
            self.logger.debug(
                f"Starting to create {self.model.__name__} with data: {item.__dict__}"
            )
            try:
                session.add(item)
                await session.commit()
                await session.refresh(item)
                self.logger.info(
                    f"{self.model.__name__} created successfully: {item.__dict__}"
                )
                return item
            except IntegrityError as ex:
                self.logger.error(
                    f"Integrity error creating {self.model.__name__}: {ex}",
                    exc_info=True,
                )
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                raise

    async def get_all_elements(self):
        async with self.db.async_session() as session:
            stmt = select(self.model)

            items = await session.execute(stmt)
            result = items.scalars().all()
            self.logger.debug(
                f"Fetched list of {len(result)} elements for {self.model.__name__}"
            )
            return list(result)

    async def get_by_id(self, item_id: int):
        self.logger.debug(
            f"Starting to fetch element with ID: {item_id} for {self.model.__name__}"
        )
        try:
            async with self.db.async_session() as session:
                result = await session.execute(
                    select(self.model).where(self.model.id == item_id)
                )
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
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(
                f"Data error fetching element with ID: {item_id} for {self.model.__name__}: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided",
            )
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error in {self.__class__.__name__}.get_by_id({item_id}): {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
            )

    async def get_by_id_and_model(
        self,
        model,
        item_id: int,
    ):
        self.logger.debug(
            f"Starting to fetch element with ID: {item_id} for {model.__name__}"
        )
        try:
            async with self.db.async_session() as session:
                result = await session.execute(select(model).where(model.id == item_id))
                item = result.scalars().one_or_none()
                if item is not None:
                    self.logger.debug(
                        f"Fetched element with ID {item_id} for {model.__name__}: {item.__dict__}"
                    )
                else:
                    self.logger.warning(
                        f"No element found with ID: {item_id} for {model.__name__}"
                    )
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
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(
                f"Data error fetching element with ID: {item_id} for {model.__name__}: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided",
            )
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error in {self.__class__.__name__}.get_by_id_and_model({item_id}): {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
            )

    async def update(self, item_id: int, item, **kwargs):
        self.logger.debug(f"Starting to update element with ID: {item_id}")
        async with self.db.async_session() as session:
            try:
                result = await session.execute(
                    select(self.model).where(self.model.id == item_id)
                )
                updated_item = result.scalars().one_or_none()

                if not updated_item:
                    self.logger.warning(
                        f"No element found with ID: {item_id} for model {self.model.__name__}"
                    )
                    raise HTTPException(
                        status_code=404,
                        detail=f"{self.model.__name__} with id {item_id} not found",
                    )

                update_data = item.model_dump(exclude_unset=True, exclude_none=True)

                for key, value in update_data.items():
                    setattr(updated_item, key, value)

                await session.flush()
                await session.commit()
                await session.refresh(updated_item)

                self.logger.debug(
                    f"Updated element with ID: {item_id}: {updated_item.__dict__}"
                )
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
                )
            except (ValueError, KeyError, TypeError) as ex:
                self.logger.warning(
                    f"Data error updating element with ID: {item_id} for {self.model.__name__}: {ex}",
                    exc_info=True,
                )
                await session.rollback()
                raise HTTPException(
                    status_code=400,
                    detail="Invalid data provided",
                )
            except Exception as ex:
                self.logger.critical(
                    f"Unexpected error in {self.__class__.__name__}.update({item_id}): {ex}",
                    exc_info=True,
                )
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error",
                )

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
                self.logger.info(
                    f"Deleted element with ID: {item_id}: {db_item.__dict__}"
                )
                return db_item
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
                )
            except (ValueError, KeyError, TypeError) as ex:
                self.logger.warning(
                    f"Data error deleting element with ID: {item_id} for {self.model.__name__}: {ex}",
                    exc_info=True,
                )
                await session.rollback()
                raise HTTPException(
                    status_code=400,
                    detail="Invalid data provided",
                )
            except Exception as ex:
                self.logger.critical(
                    f"Unexpected error in {self.__class__.__name__}.delete({item_id}): {ex}",
                    exc_info=True,
                )
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error",
                )
