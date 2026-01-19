from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.core.schema_helpers import PaginationMetadata

"""User domain schemas."""


class UserSchemaCreate(BaseModel):
    """User creation schema."""

    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    person_id: int | None = None


class UserSchemaUpdate(BaseModel):
    """User update schema."""

    email: EmailStr | None = None
    is_active: bool | None = None


class UserSchema(BaseModel):
    """User response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    is_active: bool
    person_id: int | None = None
    roles: list[str] = []
    created: datetime
    last_online: datetime | None = None
    is_online: bool


class UserChangePassword(BaseModel):
    """User password change schema."""

    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class UserAssignRole(BaseModel):
    """Assign role to user schema."""

    role_id: int


class AdminPasswordChange(BaseModel):
    """Admin password change schema (no old password required)."""

    new_password: str = Field(..., min_length=6)


class PaginatedUserResponse(BaseModel):
    data: list[UserSchema]
    metadata: PaginationMetadata
