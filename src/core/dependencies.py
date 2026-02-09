"""FastAPI dependency injection for service layer.

This module provides dependency functions and annotated type aliases for all
registered services, enabling FastAPI's native Depends() dependency injection.
"""

from typing import Annotated, Any

from fastapi import Depends

from src.core.service_registry import get_service_registry


def get_sport_service():
    registry = get_service_registry()
    return registry.get("sport")


def get_season_service():
    registry = get_service_registry()
    return registry.get("season")


def get_tournament_service():
    registry = get_service_registry()
    return registry.get("tournament")


def get_team_service():
    registry = get_service_registry()
    return registry.get("team")


def get_match_service():
    registry = get_service_registry()
    return registry.get("match")


def get_player_service():
    registry = get_service_registry()
    return registry.get("player")


def get_person_service():
    registry = get_service_registry()
    return registry.get("person")


def get_player_match_service():
    registry = get_service_registry()
    return registry.get("player_match")


def get_player_team_tournament_service():
    registry = get_service_registry()
    return registry.get("player_team_tournament")


def get_team_tournament_service():
    registry = get_service_registry()
    return registry.get("team_tournament")


def get_position_service():
    registry = get_service_registry()
    return registry.get("position")


def get_sponsor_service():
    registry = get_service_registry()
    return registry.get("sponsor")


def get_sponsor_line_service():
    registry = get_service_registry()
    return registry.get("sponsor_line")


def get_sponsor_sponsor_line_service():
    registry = get_service_registry()
    return registry.get("sponsor_sponsor_line")


def get_matchdata_service():
    registry = get_service_registry()
    return registry.get("matchdata")


def get_playclock_service():
    registry = get_service_registry()
    return registry.get("playclock")


def get_gameclock_service():
    registry = get_service_registry()
    return registry.get("gameclock")


def get_scoreboard_service():
    registry = get_service_registry()
    return registry.get("scoreboard")


def get_football_event_service():
    registry = get_service_registry()
    return registry.get("football_event")


def get_match_stats_service():
    registry = get_service_registry()
    return registry.get("match_stats")


def get_match_data_cache_service():
    registry = get_service_registry()
    return registry.get("match_data_cache")


def get_user_service():
    registry = get_service_registry()
    return registry.get("user")


def get_global_setting_service():
    registry = get_service_registry()
    return registry.get("global_setting")


def get_role_service():
    registry = get_service_registry()
    return registry.get("role")


def get_sport_scoreboard_preset_service():
    registry = get_service_registry()
    return registry.get("sport_scoreboard_preset")


SportService = Annotated[Any, Depends(get_sport_service)]
SeasonService = Annotated[Any, Depends(get_season_service)]
TournamentService = Annotated[Any, Depends(get_tournament_service)]
TeamService = Annotated[Any, Depends(get_team_service)]
MatchService = Annotated[Any, Depends(get_match_service)]
PlayerService = Annotated[Any, Depends(get_player_service)]
PersonService = Annotated[Any, Depends(get_person_service)]
PlayerMatchService = Annotated[Any, Depends(get_player_match_service)]
PlayerTeamTournamentService = Annotated[Any, Depends(get_player_team_tournament_service)]
TeamTournamentService = Annotated[Any, Depends(get_team_tournament_service)]
PositionService = Annotated[Any, Depends(get_position_service)]
SponsorService = Annotated[Any, Depends(get_sponsor_service)]
SponsorLineService = Annotated[Any, Depends(get_sponsor_line_service)]
SponsorSponsorLineService = Annotated[Any, Depends(get_sponsor_sponsor_line_service)]
MatchDataService = Annotated[Any, Depends(get_matchdata_service)]
PlayClockService = Annotated[Any, Depends(get_playclock_service)]
GameClockService = Annotated[Any, Depends(get_gameclock_service)]
ScoreboardService = Annotated[Any, Depends(get_scoreboard_service)]
FootballEventService = Annotated[Any, Depends(get_football_event_service)]
MatchStatsService = Annotated[Any, Depends(get_match_stats_service)]
MatchDataCacheService = Annotated[Any, Depends(get_match_data_cache_service)]
UserService = Annotated[Any, Depends(get_user_service)]
GlobalSettingService = Annotated[Any, Depends(get_global_setting_service)]
RoleService = Annotated[Any, Depends(get_role_service)]
SportScoreboardPresetService = Annotated[Any, Depends(get_sport_scoreboard_preset_service)]
