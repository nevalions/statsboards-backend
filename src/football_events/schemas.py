from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict


class FootballEventSchemaBase(BaseModel):
    match_id: int | None = None

    event_number: int | None = None
    event_qtr: int | None = None
    ball_on: int | None = None
    offense_team: int | None = None
    event_qb: int | None = None
    event_down: int | None = None
    event_distance: int | None = None

    event_hash: Annotated[str, Path(max_length=150)] | None = None
    play_type: Annotated[str, Path(max_length=150)] | None = None
    play_result: Annotated[str, Path(max_length=150)] | None = None

    run_player: int | None = None
    pass_received_player: int | None = None
    pass_dropped_player: int | None = None
    pass_deflected_player: int | None = None
    pass_intercepted_player: int | None = None
    fumble_player: int | None = None
    fumble_recovered_player: int | None = None
    tackle_player: int | None = None
    sack_player: int | None = None
    kick_player: int | None = None
    punt_player: int | None = None


class FootballEventSchemaUpdate(BaseModel):
    match_id: int | None = None

    event_number: int | None = None
    event_qtr: int | None = None
    ball_on: int | None = None
    offense_team: int | None = None
    event_qb: int | None = None
    event_down: int | None = None
    event_distance: int | None = None

    event_hash: str | None = None
    play_type: str | None = None
    play_result: str | None = None

    run_player: int | None = None
    pass_received_player: int | None = None
    pass_dropped_player: int | None = None
    pass_deflected_player: int | None = None
    pass_intercepted_player: int | None = None
    fumble_player: int | None = None
    fumble_recovered_player: int | None = None
    tackle_player: int | None = None
    sack_player: int | None = None
    kick_player: int | None = None
    punt_player: int | None = None


class FootballEventSchemaCreate(FootballEventSchemaBase):
    pass


class FootballEventSchema(FootballEventSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
