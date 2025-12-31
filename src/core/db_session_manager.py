import logging
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Callable

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.logging_config import get_logger

logger = get_logger("backend_logger_db_session_manager")


@asynccontextmanager
async def db_session_context(db_async_session: Callable[[], AsyncSession]):
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


def with_db_session(db_property: str = "db"):
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            db = getattr(self, db_property)
            async with db_session_context(db.async_session) as session:
                return await func(self, session, *args, **kwargs)

        return wrapper

    return decorator
