from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, ConfigDict
from starlette import status

T = TypeVar("T", bound=BaseModel)


class ResponseModel(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    content: Optional[T] = None
    type: str = "text"
    message: str
    status_code: int
    success: bool

    @classmethod
    def success_response(
        cls, content: T, message: str = "Operation successful"
    ) -> "ResponseModel[T]":
        return cls(
            content=content,
            type="text",
            message=message,
            status_code=status.HTTP_200_OK,
            success=True,
        )

    @classmethod
    def created_response(
        cls, content: T, message: str = "Resource created"
    ) -> "ResponseModel[T]":
        return cls(
            content=content,
            type="text",
            message=message,
            status_code=status.HTTP_201_CREATED,
            success=True,
        )

    @classmethod
    def not_found_response(cls, message: str = "Resource not found") -> dict[str, Any]:
        return {
            "content": None,
            "type": "text",
            "message": message,
            "status_code": status.HTTP_404_NOT_FOUND,
            "success": False,
        }
