from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import make_fields_optional


class SponsorSponsorLineSchemaBase(BaseModel):
    sponsor_line_id: int
    sponsor_id: int
    position: int | None = 1


SponsorSponsorLineSchemaUpdate = make_fields_optional(SponsorSponsorLineSchemaBase)


class SponsorSponsorLineSchemaCreate(SponsorSponsorLineSchemaBase):
    pass


class SponsorSponsorLineSchema(SponsorSponsorLineSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
