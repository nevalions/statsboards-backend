from pydantic import BaseModel, ConfigDict

from src.core.schema_helpers import make_fields_optional


class TeamTournamentSchemaBase(BaseModel):
    tournament_id: int
    team_id: int


TeamTournamentSchemaUpdate = make_fields_optional(TeamTournamentSchemaBase)


class TeamTournamentSchemaCreate(TeamTournamentSchemaBase):
    pass


class TeamTournamentSchema(TeamTournamentSchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
