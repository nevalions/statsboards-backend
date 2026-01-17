from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.core.schema_helpers import PaginationMetadata


class RoleSchemaCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: str | None = None


class RoleSchemaUpdate(BaseModel):
    description: str | None = None


class RoleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    user_count: int = 0


class PaginatedRoleResponse(BaseModel):
    data: list[RoleSchema]
    metadata: PaginationMetadata
