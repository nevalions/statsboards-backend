from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict


class FootballEventSchemaBase(BaseModel):
    match_id: int | None = None

    event_number: int | None = None
    event_qtr: int | None = None
    ball_on: int | None = None
    ball_moved_to: int | None = None
    ball_picked_on: int | None = None
    ball_kicked_to: int | None = None
    ball_returned_to: int | None = None
    ball_picked_on_fumble: int | None = None
    ball_returned_to_on_fumble: int | None = None
    offense_team: int | None = None
    event_qb: int | None = None
    event_down: int | None = None
    event_distance: int | None = None
    distance_on_offence: int | None = None

    event_hash: Annotated[str, Path(max_length=150)] | None = None
    play_direction: Annotated[str, Path(max_length=150)] | None = None
    event_strong_side: Annotated[str, Path(max_length=150)] | None = None
    play_type: Annotated[str, Path(max_length=150)] | None = None
    play_result: Annotated[str, Path(max_length=150)] | None = None
    score_result: Annotated[str, Path(max_length=150)] | None = None

    is_fumble: bool | None = False
    is_fumble_recovered: bool | None = False

    run_player: int | None = None
    pass_received_player: int | None = None
    pass_dropped_player: int | None = None
    pass_deflected_player: int | None = None
    pass_intercepted_player: int | None = None
    fumble_player: int | None = None
    fumble_recovered_player: int | None = None
    tackle_player: int | None = None
    assist_tackle_player: int | None = None
    sack_player: int | None = None
    score_player: int | None = None
    defence_score_player: int | None = None
    kickoff_player: int | None = None
    return_player: int | None = None
    pat_one_player: int | None = None
    flagged_player: int | None = None
    kick_player: int | None = None
    punt_player: int | None = None


class FootballEventSchemaUpdate(BaseModel):
    match_id: int | None = None

    event_number: int | None = None
    event_qtr: int | None = None
    ball_on: int | None = None
    ball_moved_to: int | None = None
    ball_picked_on: int | None = None
    ball_kicked_to: int | None = None
    ball_returned_to: int | None = None
    ball_picked_on_fumble: int | None = None
    ball_returned_to_on_fumble: int | None = None
    offense_team: int | None = None
    event_qb: int | None = None
    event_down: int | None = None
    event_distance: int | None = None
    distance_on_offence: int | None = None

    event_hash: str | None = None
    play_direction: str | None = None
    event_strong_side: str | None = None
    play_type: str | None = None
    play_result: str | None = None
    score_result: str | None = None

    is_fumble: bool | None = None
    is_fumble_recovered: bool | None = None

    run_player: int | None = None
    pass_received_player: int | None = None
    pass_dropped_player: int | None = None
    pass_deflected_player: int | None = None
    pass_intercepted_player: int | None = None
    fumble_player: int | None = None
    fumble_recovered_player: int | None = None
    tackle_player: int | None = None
    assist_tackle_player: int | None = None
    sack_player: int | None = None
    score_player: int | None = None
    defence_score_player: int | None = None
    kickoff_player: int | None = None
    return_player: int | None = None
    pat_one_player: int | None = None
    flagged_player: int | None = None
    kick_player: int | None = None
    punt_player: int | None = None


class FootballEventSchemaCreate(FootballEventSchemaBase):
    pass


class FootballEventSchema(FootballEventSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
