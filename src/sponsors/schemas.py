from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import make_fields_optional


class SponsorSchemaBase(BaseModel):
    title: Annotated[str, Path(max_length=50)]
    logo_url: str | None = ""
    scale_logo: float | None = 1.0


SponsorSchemaUpdate = make_fields_optional(SponsorSchemaBase)


class SponsorSchemaCreate(SponsorSchemaBase):
    pass


class SponsorSchema(SponsorSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class UploadSponsorLogoResponse(BaseModel):
    logoUrl: str
