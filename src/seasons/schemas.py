from pydantic import BaseModel, ConfigDict


class SeasonSchemaBase(BaseModel):
    year: int
    description: str | None = None


class SeasonSchemaUpdate(BaseModel):
    year: int | None = None
    description: str | None = None


class SeasonSchemaCreate(SeasonSchemaBase):
    pass


class SeasonSchema(SeasonSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
