from pydantic import BaseModel, ConfigDict


class SponsorSponsorLineSchemaBase(BaseModel):
    sponsor_line_id: int
    sponsor_id: int
    position: int | None = 1


class SponsorSponsorLineSchemaUpdate(BaseModel):
    sponsor_line_id: int | None = None
    sponsor_id: int | None = None
    position: int | None = None


class SponsorSponsorLineSchemaCreate(SponsorSponsorLineSchemaBase):
    pass


class SponsorSponsorLineSchema(SponsorSponsorLineSchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
