from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict, Field


class FootballEventSchemaBase(BaseModel):
    match_id: int | None = Field(None, examples=[1])

    event_number: int | None = Field(None, examples=[1, 2, 3])
    event_qtr: int | None = Field(None, examples=[1, 2, 3, 4])
    ball_on: int | None = Field(None, examples=[25, 50, 75])
    ball_moved_to: int | None = Field(None, examples=[30, 55, 80])
    ball_picked_on: int | None = Field(None, examples=[25, 50])
    ball_kicked_to: int | None = Field(None, examples=[20, 45])
    ball_returned_to: int | None = Field(None, examples=[30, 60])
    ball_picked_on_fumble: int | None = Field(None, examples=[35, 70])
    ball_returned_to_on_fumble: int | None = Field(None, examples=[40, 75])
    offense_team: int | None = Field(None, examples=[1])
    event_qb: int | None = Field(None, examples=[10])
    event_down: int | None = Field(None, examples=[1, 2, 3, 4])
    event_distance: int | None = Field(None, examples=[10, 5])
    distance_on_offence: int | None = Field(None, examples=[5, 15])

    event_hash: Annotated[str, Path(max_length=150)] | None = Field(None, examples=["abc123"])
    play_direction: Annotated[str, Path(max_length=150)] | None = Field(None, examples=["left", "right", "middle"])
    event_strong_side: Annotated[str, Path(max_length=150)] | None = Field(None, examples=["left", "right"])
    play_type: Annotated[str, Path(max_length=150)] | None = Field(None, examples=["run", "pass", "kick", "punt"])
    play_result: Annotated[str, Path(max_length=150)] | None = Field(None, examples=["gain", "loss", "incomplete", "interception"])
    score_result: Annotated[str, Path(max_length=150)] | None = Field(None, examples=["touchdown", "field_goal", "none"])

    is_fumble: bool | None = Field(False, examples=[True, False])
    is_fumble_recovered: bool | None = Field(False, examples=[True, False])

    run_player: int | None = Field(None, examples=[5])
    pass_received_player: int | None = Field(None, examples=[8])
    pass_dropped_player: int | None = Field(None, examples=[8])
    pass_deflected_player: int | None = Field(None, examples=[15])
    pass_intercepted_player: int | None = Field(None, examples=[22])
    fumble_player: int | None = Field(None, examples=[5])
    fumble_recovered_player: int | None = Field(None, examples=[12])
    tackle_player: int | None = Field(None, examples=[30])
    assist_tackle_player: int | None = Field(None, examples=[28])
    sack_player: int | None = Field(None, examples=[45])
    score_player: int | None = Field(None, examples=[5])
    defence_score_player: int | None = Field(None, examples=[22])
    kickoff_player: int | None = Field(None, examples=[3])
    return_player: int | None = Field(None, examples=[20])
    pat_one_player: int | None = Field(None, examples=[8])
    flagged_player: int | None = Field(None, examples=[55])
    kick_player: int | None = Field(None, examples=[3])
    punt_player: int | None = Field(None, examples=[2])


class FootballEventSchemaUpdate(BaseModel):
    match_id: int | None = Field(None, examples=[1])

    event_number: int | None = Field(None, examples=[1, 2, 3])
    event_qtr: int | None = Field(None, examples=[1, 2, 3, 4])
    ball_on: int | None = Field(None, examples=[25, 50, 75])
    ball_moved_to: int | None = Field(None, examples=[30, 55, 80])
    ball_picked_on: int | None = Field(None, examples=[25, 50])
    ball_kicked_to: int | None = Field(None, examples=[20, 45])
    ball_returned_to: int | None = Field(None, examples=[30, 60])
    ball_picked_on_fumble: int | None = Field(None, examples=[35, 70])
    ball_returned_to_on_fumble: int | None = Field(None, examples=[40, 75])
    offense_team: int | None = Field(None, examples=[1])
    event_qb: int | None = Field(None, examples=[10])
    event_down: int | None = Field(None, examples=[1, 2, 3, 4])
    event_distance: int | None = Field(None, examples=[10, 5])
    distance_on_offence: int | None = Field(None, examples=[5, 15])

    event_hash: str | None = Field(None, examples=["abc123"])
    play_direction: str | None = Field(None, examples=["left", "right", "middle"])
    event_strong_side: str | None = Field(None, examples=["left", "right"])
    play_type: str | None = Field(None, examples=["run", "pass", "kick", "punt"])
    play_result: str | None = Field(None, examples=["gain", "loss", "incomplete", "interception"])
    score_result: str | None = Field(None, examples=["touchdown", "field_goal", "none"])

    is_fumble: bool | None = Field(None, examples=[True, False])
    is_fumble_recovered: bool | None = Field(None, examples=[True, False])

    run_player: int | None = Field(None, examples=[5])
    pass_received_player: int | None = Field(None, examples=[8])
    pass_dropped_player: int | None = Field(None, examples=[8])
    pass_deflected_player: int | None = Field(None, examples=[15])
    pass_intercepted_player: int | None = Field(None, examples=[22])
    fumble_player: int | None = Field(None, examples=[5])
    fumble_recovered_player: int | None = Field(None, examples=[12])
    tackle_player: int | None = Field(None, examples=[30])
    assist_tackle_player: int | None = Field(None, examples=[28])
    sack_player: int | None = Field(None, examples=[45])
    score_player: int | None = Field(None, examples=[5])
    defence_score_player: int | None = Field(None, examples=[22])
    kickoff_player: int | None = Field(None, examples=[3])
    return_player: int | None = Field(None, examples=[20])
    pat_one_player: int | None = Field(None, examples=[8])
    flagged_player: int | None = Field(None, examples=[55])
    kick_player: int | None = Field(None, examples=[3])
    punt_player: int | None = Field(None, examples=[2])


class FootballEventSchemaCreate(FootballEventSchemaBase):
    pass


class FootballEventSchema(FootballEventSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., examples=[1])
