"""Authentication and authorization schemas."""

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT token response schema."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded JWT token data schema."""

    user_id: int | None = None
    username: str | None = None


class UserLogin(BaseModel):
    """User login request schema."""

    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class UserCreate(BaseModel):
    """User creation request schema."""

    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    person_id: int | None = None


class UserUpdate(BaseModel):
    """User update request schema."""

    email: EmailStr | None = None
    password: str | None = Field(None, min_length=6)
    is_active: bool | None = None


class UserResponse(BaseModel):
    """User response schema."""

    id: int
    username: str
    email: str
    is_active: bool
    person_id: int | None = None
    roles: list[str] = []

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    """Role creation request schema."""

    name: str = Field(..., min_length=2, max_length=50)
    description: str | None = None


class RoleUpdate(BaseModel):
    """Role update request schema."""

    description: str | None = None


class RoleResponse(BaseModel):
    """Role response schema."""

    id: int
    name: str
    description: str | None = None
    user_count: int = 0

    class Config:
        from_attributes = True


class UserRoleAssign(BaseModel):
    """Assign role to user request schema."""

    role_id: int
