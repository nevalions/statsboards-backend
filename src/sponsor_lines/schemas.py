from fastapi import Path
from pydantic import BaseModel, ConfigDict
from typing import Annotated


class SponsorLineSchemaBase(BaseModel):
    title: Annotated[str, Path(max_length=50)] = 'Sponsor Line'
    is_visible: bool | None = False


class SponsorLineSchemaUpdate(BaseModel):
    title: str | None = None
    is_visible: bool | None = False


class SponsorLineSchemaCreate(SponsorLineSchemaBase):
    pass


class SponsorLineSchema(SponsorLineSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
