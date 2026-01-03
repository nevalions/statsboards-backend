from datetime import datetime as date_type
from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import make_fields_optional


class PersonSchemaBase(BaseModel):
    first_name: Annotated[str, Path(max_length=100)] = "Name"
    second_name: Annotated[str, Path(max_length=100)] | None = "Surname"
    person_photo_url: Annotated[str, Path(max_length=500)] | None = ""
    person_photo_icon_url: Annotated[str, Path(max_length=500)] | None = ""
    person_photo_web_url: Annotated[str, Path(max_length=500)] | None = ""
    person_dob: date_type | None = None
    person_eesl_id: int | None = None


PersonSchemaUpdate = make_fields_optional(PersonSchemaBase)


class PersonSchemaCreate(PersonSchemaBase):
    pass


class PersonSchema(PersonSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class UploadPersonPhotoResponse(BaseModel):
    photoUrl: str


class UploadResizePersonPhotoResponse(BaseModel):
    original: str
    icon: str
    webview: str
