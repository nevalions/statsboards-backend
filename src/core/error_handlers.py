from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from src.logging_config import get_logger


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
            detail=f"{self.model_name} with {field_name} {item_id} not found",
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
                detail=f"Database constraint violation: {str(error)}",
            )
        elif isinstance(error, SQLAlchemyError):
            raise HTTPException(status_code=500, detail=f"Database error: {str(error)}")
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error")
