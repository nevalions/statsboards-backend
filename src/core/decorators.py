import asyncio
import functools
from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions import (
    BusinessLogicError,
    NotFoundError,
)

T = TypeVar("T")


def handle_service_exceptions(
    item_name: str | None = None,
    operation: str = "operation",
    reraise_not_found: bool = False,
    return_value_on_not_found: T | None = None,
):
    def decorator(method: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(method)
        async def async_wrapper(self: object, *args: object, **kwargs: object) -> T | None:
            logger = getattr(self, "logger", None)
            model = getattr(self, "model", None)
            actual_item_name = item_name or (model.__name__ if model else "item")

            try:
                return await method(self, *args, **kwargs)
            except HTTPException:
                raise
            except IntegrityError as ex:
                if logger:
                    logger.error(
                        f"Integrity error {operation} {actual_item_name}: {ex}",
                        exc_info=True,
                    )
                raise HTTPException(
                    status_code=409,
                    detail=f"Conflict {operation} {model.__name__ if model else actual_item_name}",
                )
            except SQLAlchemyError as ex:
                if logger:
                    logger.error(
                        f"Database error {operation} {actual_item_name}: {ex}",
                        exc_info=True,
                    )
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error {operation} {model.__name__ if model else actual_item_name}",
                )
            except (ValueError, KeyError, TypeError) as ex:
                if logger:
                    logger.warning(
                        f"Data error {operation} {actual_item_name}: {ex}",
                        exc_info=True,
                    )
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid data provided for {actual_item_name}",
                )
            except NotFoundError as ex:
                if logger:
                    logger.info(
                        f"Not found {operation} {actual_item_name}: {ex}",
                        exc_info=True,
                    )
                if reraise_not_found:
                    raise HTTPException(status_code=404, detail="Resource not found")
                return return_value_on_not_found
            except BusinessLogicError as ex:
                if logger:
                    logger.error(
                        f"Business logic error {operation} {actual_item_name}: {ex}",
                        exc_info=True,
                    )
                raise HTTPException(status_code=422, detail="Business logic error")
            except Exception as ex:
                if logger:
                    logger.critical(
                        f"Unexpected error in {self.__class__.__name__}.{method.__name__}: {ex}",
                        exc_info=True,
                    )
                raise HTTPException(status_code=500, detail="Internal server error")

        @functools.wraps(method)
        def sync_wrapper(self: object, *args: object, **kwargs: object) -> T | None:
            logger = getattr(self, "logger", None)
            model = getattr(self, "model", None)
            actual_item_name = item_name or (model.__name__ if model else "item")

            try:
                return method(self, *args, **kwargs)
            except HTTPException:
                raise
            except IntegrityError as ex:
                if logger:
                    logger.error(
                        f"Integrity error {operation} {actual_item_name}: {ex}",
                        exc_info=True,
                    )
                raise HTTPException(
                    status_code=409,
                    detail=f"Conflict {operation} {model.__name__ if model else actual_item_name}",
                )
            except SQLAlchemyError as ex:
                if logger:
                    logger.error(
                        f"Database error {operation} {actual_item_name}: {ex}",
                        exc_info=True,
                    )
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error {operation} {model.__name__ if model else actual_item_name}",
                )
            except (ValueError, KeyError, TypeError) as ex:
                if logger:
                    logger.warning(
                        f"Data error {operation} {actual_item_name}: {ex}",
                        exc_info=True,
                    )
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid data provided for {actual_item_name}",
                )
            except NotFoundError as ex:
                if logger:
                    logger.info(
                        f"Not found {operation} {actual_item_name}: {ex}",
                        exc_info=True,
                    )
                if reraise_not_found:
                    raise HTTPException(status_code=404, detail="Resource not found")
                return return_value_on_not_found
            except BusinessLogicError as ex:
                if logger:
                    logger.error(
                        f"Business logic error {operation} {actual_item_name}: {ex}",
                        exc_info=True,
                    )
                raise HTTPException(status_code=422, detail="Business logic error")
            except Exception as ex:
                if logger:
                    logger.critical(
                        f"Unexpected error in {self.__class__.__name__}.{method.__name__}: {ex}",
                        exc_info=True,
                    )
                raise HTTPException(status_code=500, detail="Internal server error")

        return async_wrapper if asyncio.iscoroutinefunction(method) else sync_wrapper

    return decorator


def handle_view_exceptions(
    error_message: str = "Internal server error",
    status_code: int = 500,
):
    """
    Decorator for view endpoints to handle exceptions with consistent logging and error responses.

    This decorator catches exceptions in view endpoints, logs them, and converts them to
    HTTPException with specified error message and status code. HTTPException is
    re-raised as-is to preserve its status code and message.

    Args:
        error_message: The error detail to use for non-HTTPException errors
        status_code: The HTTP status code to use for non-HTTPException errors

    Example:
        @handle_view_exceptions(error_message="Error uploading file", status_code=500)
        async def upload_endpoint(file: UploadFile):
            return await file_service.save(file)
    """

    def decorator(method: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(method)
        async def async_wrapper(*args: object, **kwargs: object) -> Any:
            logger = None
            if args and hasattr(args[0], "logger"):
                logger = getattr(args[0], "logger", None)

            try:
                return await method(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as ex:
                if logger:
                    logger.error(
                        f"{error_message}: {ex}",
                        exc_info=True,
                    )
                raise HTTPException(
                    status_code=status_code,
                    detail=error_message,
                ) from ex

        return async_wrapper

    return decorator
