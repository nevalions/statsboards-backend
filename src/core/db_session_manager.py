from collections.abc import AsyncGenerator, Callable, Coroutine
from contextlib import asynccontextmanager
from functools import wraps
from typing import TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.logging_config import get_logger

logger = get_logger("backend_logger_db_session_manager")

T = TypeVar("T")


def _is_test_session_maker(session_maker: Callable[[], AsyncSession]) -> bool:
    """Check if session maker is a test session maker (not a production session).

    Test session makers are typically lambda or have different characteristics
    than production async_sessionmaker instances.
    """
    try:
        from src.core.models.base import db

        return session_maker is db.test_async_session
    except (ImportError, AttributeError):
        return False


@asynccontextmanager
async def db_session_context(
    db_async_session: Callable[[], AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    session = db_async_session()
    is_test_mode = _is_test_session_maker(db_async_session)
    try:
        yield session
        if is_test_mode:
            await session.flush()
            logger.debug("Database session flushed (test mode)")
        else:
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


def with_db_session(
    db_property: str = "db",
) -> Callable[
    [Callable[..., Coroutine[object, object, T]]], Callable[..., Coroutine[object, object, T]]
]:
    def decorator(
        func: Callable[..., Coroutine[object, object, T]],
    ) -> Callable[..., Coroutine[object, object, T]]:
        @wraps(func)
        async def wrapper(self: object, *args: object, **kwargs: object) -> T:
            db = getattr(self, db_property)
            async with db_session_context(db.get_session_maker()) as session:
                return await func(self, session, *args, **kwargs)

        return wrapper

    return decorator
