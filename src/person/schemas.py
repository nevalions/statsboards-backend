from datetime import datetime as date_type
from fastapi import Path
from pydantic import BaseModel, ConfigDict
from typing import Annotated


class PersonSchemaBase(BaseModel):
    first_name: Annotated[str, Path(max_length=100)] = 'Name'
    second_name: Annotated[str, Path(max_length=100)] | None = 'Surname'
    person_photo_url: Annotated[str, Path(max_length=500)] | None = ''
    person_dob: date_type | None = None
    person_eesl_id: int | None = None


class PersonSchemaUpdate(BaseModel):
    first_name: str | None = None
    second_name: str | None = None
    person_photo_url: str | None = None
    person_dob: date_type | None = None
    person_eesl_id: int | None = None


class PersonSchemaCreate(PersonSchemaBase):
    pass


class PersonSchema(PersonSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class UploadPersonPhotoResponse(BaseModel):
    photoUrl: str
