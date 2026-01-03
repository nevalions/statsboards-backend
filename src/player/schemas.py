from pydantic import BaseModel, ConfigDict, Field

from src.core.schema_helpers import make_fields_optional


class PlayerSchemaBase(BaseModel):
    sport_id: int | None = Field(None, examples=[1])
    person_id: int | None = Field(None, examples=[1])
    player_eesl_id: int | None = Field(None, examples=[98765])


PlayerSchemaUpdate = make_fields_optional(PlayerSchemaBase)


class PlayerSchemaCreate(PlayerSchemaBase):
    pass


class PlayerSchema(PlayerSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., examples=[1])
