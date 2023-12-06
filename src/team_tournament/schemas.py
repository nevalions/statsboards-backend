from pydantic import BaseModel, ConfigDict


class TeamTournamentSchemaBase(BaseModel):
    tournament_id: int
    team_id: int


class TeamTournamentSchemaUpdate(BaseModel):
    tournament_id: int | None = None
    team_id: int | None = None


class TeamTournamentSchemaCreate(TeamTournamentSchemaBase):
    pass


class TeamTournamentSchema(TeamTournamentSchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
