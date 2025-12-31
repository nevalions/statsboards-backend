import logging
from collections.abc import AsyncGenerator, Callable, Coroutine
from contextlib import asynccontextmanager
from functools import wraps
from typing import TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.logging_config import get_logger

logger = get_logger("backend_logger_db_session_manager")

T = TypeVar("T")


@asynccontextmanager
async def db_session_context(db_async_session: Callable[[], AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    session = db_async_session()
    try:
        yield session
        await session.commit()
        logger.debug("Database session committed successfully")
    except SQLAlchemyError as ex:
        await session.rollback()
        logger.error(f"Database session rolled back due to error: {ex}", exc_info=True)
        raise
    except Exception as ex:
        await session.rollback()
        logger.critical(
            f"Database session rolled back due to unexpected error: {ex}", exc_info=True
        )
        raise
    finally:
        await session.close()
        logger.debug("Database session closed")


def with_db_session(db_property: str = "db") -> Callable[[Callable[..., Coroutine[object, object, T]]], Callable[..., Coroutine[object, object, T]]]:
    def decorator(func: Callable[..., Coroutine[object, object, T]]) -> Callable[..., Coroutine[object, object, T]]:
        @wraps(func)
        async def wrapper(self: object, *args: object, **kwargs: object) -> T:
            db = getattr(self, db_property)
            async with db_session_context(db.async_session) as session:
                return await func(self, session, *args, **kwargs)

        return wrapper

    return decorator
