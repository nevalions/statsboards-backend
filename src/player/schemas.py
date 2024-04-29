from pydantic import BaseModel, ConfigDict


class PlayerSchemaBase(BaseModel):
    sport_id: int | None
    person_id: int | None
    player_eesl_id: int | None = None


class PlayerSchemaUpdate(BaseModel):
    sport_id: int | None = None
    person_id: int | None = None
    player_eesl_id: int | None = None


class PlayerSchemaCreate(PlayerSchemaBase):
    pass


class PlayerSchema(PlayerSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
