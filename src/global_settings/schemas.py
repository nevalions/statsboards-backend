from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.core.schema_helpers import make_fields_optional


class GlobalSettingSchemaBase(BaseModel):
    key: str = Field(..., examples=["theme.default"], max_length=100)
    value: str = Field(..., examples=["dark"])
    value_type: str = Field(..., examples=["string"], max_length=20)
    category: str | None = Field(None, examples=["ui"], max_length=50)
    description: str | None = Field(None, examples=["Default application theme"])


GlobalSettingSchemaUpdate = make_fields_optional(GlobalSettingSchemaBase)


class GlobalSettingSchemaCreate(GlobalSettingSchemaBase):
    pass


class GlobalSettingSchema(GlobalSettingSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime


class GlobalSettingValueSchema(BaseModel):
    value: str


class GlobalSettingsGroupedSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    settings: list[GlobalSettingSchema]
