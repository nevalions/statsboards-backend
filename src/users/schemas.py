"""User domain schemas."""

from pydantic import BaseModel, EmailStr, Field

from src.core.schema_helpers import PaginationMetadata


class UserSchemaCreate(BaseModel):
    """User creation schema."""

    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    person_id: int | None = None


class UserSchemaUpdate(BaseModel):
    """User update schema."""

    email: EmailStr | None = None
    password: str | None = Field(None, min_length=6)
    is_active: bool | None = None


class UserSchema(BaseModel):
    """User response schema."""

    id: int
    username: str
    email: str
    is_active: bool
    person_id: int | None = None
    roles: list[str] = []

    class Config:
        from_attributes = True


class UserChangePassword(BaseModel):
    """User password change schema."""

    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class UserAssignRole(BaseModel):
    """Assign role to user schema."""

    role_id: int


class PaginatedUserResponse(BaseModel):
    data: list[UserSchema]
    metadata: PaginationMetadata
