from fastapi import Path
from pydantic import BaseModel, ConfigDict
from typing import Annotated


class ScoreboardSchemaBase(BaseModel):
    is_qtr: bool = True
    is_time: bool = True
    is_playclock: bool = True
    is_downdistance: bool = True

    team_a_game_color: Annotated[str, Path(max_length=10)] = "#c01c28"
    team_b_game_color: Annotated[str, Path(max_length=10)] = "#1c71d8"
    use_team_a_game_color: bool = False
    use_team_b_game_color: bool = False

    team_a_game_title: Annotated[str, Path(max_length=50)] = None
    team_b_game_title: Annotated[str, Path(max_length=50)] = None
    use_team_a_game_title: bool = False
    use_team_b_game_title: bool = False

    team_a_game_logo: str | None = None
    team_b_game_logo: str | None = None
    use_team_a_game_logo: bool = False
    use_team_b_game_logo: bool = False

    scale_logo_a: float | None = 2.0
    scale_logo_b: float | None = 2.0

    match_id: int | None = None


class ScoreboardSchemaUpdate(BaseModel):
    is_qtr: bool | None = None
    is_time: bool | None = None
    is_playclock: bool | None = None
    is_downdistance: bool | None = None

    team_a_game_color: str | None = None
    team_b_game_color: str | None = None
    use_team_a_game_color: bool | None = None
    use_team_b_game_color: bool | None = None

    team_a_game_logo: str | None = None
    team_b_game_logo: str | None = None
    use_team_a_game_logo: bool | None = None
    use_team_b_game_logo: bool | None = None

    scale_logo_a: float | None = None
    scale_logo_b: float | None = None

    team_a_game_title: str | None = None
    team_b_game_title: str | None = None
    use_team_a_game_title: bool | None = None
    use_team_b_game_title: bool | None = None

    match_id: int | None = None


class ScoreboardSchemaCreate(ScoreboardSchemaBase):
    pass


class ScoreboardSchema(ScoreboardSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
