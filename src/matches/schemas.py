from __future__ import annotations

from datetime import datetime as date_type

from pydantic import BaseModel, ConfigDict, Field

from src.core.schema_helpers import PaginationMetadata, make_fields_optional
from src.core.shared_schemas import PrivacyFieldsBase, SponsorFieldsBase
from src.matchdata.schemas import MatchDataSchemaCreate
from src.scoreboards.schemas import ScoreboardSchemaCreate
from src.teams.schemas import TeamSchema
from src.tournaments.schemas import TournamentSchema


class MatchSchemaBase(SponsorFieldsBase, PrivacyFieldsBase):
    match_date: date_type | None = Field(None, examples=["2024-01-15T15:00:00"])
    week: int = Field(1, examples=[1, 2, 3])
    match_eesl_id: int | None = Field(None, examples=[12345])
    team_a_id: int = Field(..., examples=[1])
    team_b_id: int = Field(..., examples=[2])
    tournament_id: int | None = Field(None, examples=[1])


MatchSchemaUpdate = make_fields_optional(MatchSchemaBase)


class MatchSchemaCreate(MatchSchemaBase):
    model_config = ConfigDict(from_attributes=True)


class MatchSchema(MatchSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., examples=[1])


class MatchDataScoreboardSchemaCreate(BaseModel):
    match: MatchSchemaCreate
    match_data: MatchDataSchemaCreate
    scoreboard: ScoreboardSchemaCreate


class FootballOffenseStats(BaseModel):
    id: int
    pass_attempts: int = 0
    pass_received: int = 0
    pass_yards: int = 0
    pass_td: int = 0
    run_attempts: int = 0
    run_yards: int = 0
    run_avr: float = 0.0
    run_td: int = 0
    fumble: int = 0

    model_config = ConfigDict(from_attributes=True)


class FootballQBStats(BaseModel):
    id: int
    passes: int = 0
    passes_completed: int = 0
    pass_yards: int = 0
    pass_td: int = 0
    pass_avr: float = 0.0
    run_attempts: int = 0
    run_yards: int = 0
    run_td: int = 0
    run_avr: float = 0.0
    fumble: int = 0
    interception: int = 0
    qb_rating: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class FootballDefenseStats(BaseModel):
    id: int
    tackles: int = 0
    assist_tackles: int = 0
    sacks: int = 0
    interceptions: int = 0
    fumble_recoveries: int = 0
    flags: int = 0

    model_config = ConfigDict(from_attributes=True)


class FootballTeamStats(BaseModel):
    id: int
    offence_yards: int = 0
    pass_att: int = 0
    run_att: int = 0
    avg_yards_per_att: float = 0.0
    pass_yards: int = 0
    run_yards: int = 0
    lost_yards: int = 0
    flag_yards: int = 0
    third_down_attempts: int = 0
    third_down_conversions: int = 0
    fourth_down_attempts: int = 0
    fourth_down_conversions: int = 0
    first_down_gained: int = 0
    turnovers: int = 0

    model_config = ConfigDict(from_attributes=True)


class PaginatedMatchResponse(BaseModel):
    data: list[MatchSchema]
    metadata: PaginationMetadata


class MatchWithDetailsSchema(MatchSchema):
    team_a: TeamSchema | None = Field(None, description="Team A with full details")
    team_b: TeamSchema | None = Field(None, description="Team B with full details")
    tournament: TournamentSchema | None = Field(None, description="Tournament with full details")


class PaginatedMatchWithDetailsResponse(BaseModel):
    data: list[MatchWithDetailsSchema]
    metadata: PaginationMetadata
