import os

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def sanitize_error_message(error: Exception, generic_message: str = "Internal server error") -> str:
    """Return safe error message - full details only in DEBUG mode.

    Args:
        error: The exception that occurred
        generic_message: Generic message for production

    Returns:
        Safe error message string
    """
    if DEBUG:
        return str(error)
    return generic_message


class DatabaseErrorHandler:
    """Consistent error handling for database operations"""

    def __init__(self, model_name: str, logger):
        self.model_name = model_name
        self.logger = logger

    def handle_not_found(
        self,
        item_id: int | str,
        field_name: str = "id",
    ) -> None:
        """Raise 404 if item not found"""
        raise HTTPException(
            status_code=404,
            detail="Resource not found",
        )

    def handle_conflict(self, detail: str | None = None) -> None:
        """Raise 409 for conflicts"""
        raise HTTPException(
            status_code=409,
            detail=detail or f"Conflict creating {self.model_name}",
        )

    def handle_db_error(self, error: Exception, context: str = "") -> None:
        """Handle database errors with appropriate status codes"""
        self.logger.error(f"{self.model_name} {context} error: {error}", exc_info=True)

        if isinstance(error, IntegrityError):
            raise HTTPException(
                status_code=409,
                detail=sanitize_error_message(
                    error, "Resource already exists or violates constraints"
                ),
            )
        elif isinstance(error, SQLAlchemyError):
            raise HTTPException(
                status_code=500,
                detail=sanitize_error_message(error, "Database operation failed"),
            )
        else:
            raise HTTPException(status_code=500, detail="Internal server error")
