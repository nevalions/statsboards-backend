from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict


class ScoreboardSchemaBase(BaseModel):
    is_qtr: bool = True
    is_time: bool = True
    is_playclock: bool = True
    is_downdistance: bool = True
    is_tournament_logo: bool = True
    is_main_sponsor: bool = True
    is_sponsor_line: bool = True
    is_match_sponsor_line: bool = False

    is_team_a_start_offense: bool = False
    is_team_b_start_offense: bool = False
    is_team_a_start_defense: bool = False
    is_team_b_start_defense: bool = False

    is_home_match_team_lower: bool = False
    is_away_match_team_lower: bool = False

    is_football_qb_full_stats_lower: bool = False
    football_qb_full_stats_match_lower_id: int | None = None
    is_match_player_lower: bool = False
    player_match_lower_id: int | None = None

    team_a_game_color: Annotated[str, Path(max_length=10)] = "#c01c28"
    team_b_game_color: Annotated[str, Path(max_length=10)] = "#1c71d8"
    use_team_a_game_color: bool = False
    use_team_b_game_color: bool = False

    team_a_game_title: Annotated[str, Path(max_length=50)] | None = None
    team_b_game_title: Annotated[str, Path(max_length=50)] | None = None
    use_team_a_game_title: bool = False
    use_team_b_game_title: bool = False

    team_a_game_logo: str | None = None
    team_b_game_logo: str | None = None
    use_team_a_game_logo: bool = False
    use_team_b_game_logo: bool = False

    scale_tournament_logo: float | None = 2.0
    scale_main_sponsor: float | None = 2.0
    scale_logo_a: float | None = 2.0
    scale_logo_b: float | None = 2.0

    is_flag: bool | None = False
    is_goal_team_a: bool | None = False
    is_goal_team_b: bool | None = False
    is_timeout_team_a: bool | None = False
    is_timeout_team_b: bool | None = False

    match_id: int | None = None


class ScoreboardSchemaUpdate(BaseModel):
    is_qtr: bool | None = None
    is_time: bool | None = None
    is_playclock: bool | None = None
    is_downdistance: bool | None = None
    is_tournament_logo: bool | None = None
    is_main_sponsor: bool | None = None
    is_sponsor_line: bool | None = None
    is_match_sponsor_line: bool | None = None

    is_team_a_start_offense: bool | None = None
    is_team_b_start_offense: bool | None = None
    is_team_a_start_defense: bool | None = None
    is_team_b_start_defense: bool | None = None

    is_home_match_team_lower: bool | None = None
    is_away_match_team_lower: bool | None = None

    is_football_qb_full_stats_lower: bool | None = None
    football_qb_full_stats_match_lower_id: int | None = None
    is_match_player_lower: bool | None = None
    player_match_lower_id: int | None = None

    team_a_game_color: str | None = None
    team_b_game_color: str | None = None
    use_team_a_game_color: bool | None = None
    use_team_b_game_color: bool | None = None

    team_a_game_logo: str | None = None
    team_b_game_logo: str | None = None
    use_team_a_game_logo: bool | None = None
    use_team_b_game_logo: bool | None = None

    scale_tournament_logo: float | None = None
    scale_main_sponsor: float | None = None
    scale_logo_a: float | None = None
    scale_logo_b: float | None = None

    team_a_game_title: str | None = None
    team_b_game_title: str | None = None
    use_team_a_game_title: bool | None = None
    use_team_b_game_title: bool | None = None

    is_flag: bool | None = None
    is_goal_team_a: bool | None = None
    is_goal_team_b: bool | None = None
    is_timeout_team_a: bool | None = False
    is_timeout_team_b: bool | None = False

    match_id: int | None = None


class ScoreboardSchemaCreate(ScoreboardSchemaBase):
    pass


class ScoreboardSchema(ScoreboardSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
