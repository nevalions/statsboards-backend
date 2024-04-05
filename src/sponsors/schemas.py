from fastapi import Path
from pydantic import BaseModel, ConfigDict
from typing import Annotated


class SponsorSchemaBase(BaseModel):
    title: Annotated[str, Path(max_length=50)]
    logo_url: str | None = ''


class SponsorSchemaUpdate(BaseModel):
    title: str | None = None
    logo_url: str | None = None


class SponsorSchemaCreate(SponsorSchemaBase):
    pass


class SponsorSchema(SponsorSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class UploadSponsorLogoResponse(BaseModel):
    logoUrl: str
