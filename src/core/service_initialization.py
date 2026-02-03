"""Service initialization and registration module.

This module handles the registration of all service factories with the
global service registry, enabling dependency injection and decoupling
services from each other.
"""

from typing import Any, Callable

from src.core.models import BaseServiceDB
from src.core.models.base import Database
from src.core.service_registry import ServiceRegistry, get_service_registry, register_service

ServiceFactory = Callable[[Database], Any]
ServiceDefinition = tuple[str, ServiceFactory, bool]


def _sport_factory(database: Database) -> BaseServiceDB:
    from src.sports.db_services import SportServiceDB

    return SportServiceDB(database)


def _season_factory(database: Database) -> BaseServiceDB:
    from src.seasons.db_services import SeasonServiceDB

    return SeasonServiceDB(database)


def _tournament_factory(database: Database) -> BaseServiceDB:
    from src.tournaments.db_services import TournamentServiceDB

    return TournamentServiceDB(database)


def _team_factory(database: Database) -> BaseServiceDB:
    from src.teams.db_services import TeamServiceDB

    return TeamServiceDB(database)


def _match_factory(database: Database) -> BaseServiceDB:
    from src.matches.db_services import MatchServiceDB

    return MatchServiceDB(database)


def _player_factory(database: Database) -> BaseServiceDB:
    from src.player.db_services import PlayerServiceDB

    return PlayerServiceDB(database)


def _person_factory(database: Database) -> BaseServiceDB:
    from src.person.db_services import PersonServiceDB

    return PersonServiceDB(database)


def _player_match_factory(database: Database) -> BaseServiceDB:
    from src.player_match.db_services import PlayerMatchServiceDB

    return PlayerMatchServiceDB(database)


def _player_team_tournament_factory(database: Database) -> BaseServiceDB:
    from src.player_team_tournament.db_services import PlayerTeamTournamentServiceDB

    return PlayerTeamTournamentServiceDB(database)


def _team_tournament_factory(database: Database) -> BaseServiceDB:
    from src.team_tournament.db_services import TeamTournamentServiceDB

    return TeamTournamentServiceDB(database)


def _position_factory(database: Database) -> BaseServiceDB:
    from src.positions.db_services import PositionServiceDB

    return PositionServiceDB(database)


def _sponsor_factory(database: Database) -> BaseServiceDB:
    from src.sponsors.db_services import SponsorServiceDB

    return SponsorServiceDB(database)


def _sponsor_line_factory(database: Database) -> BaseServiceDB:
    from src.sponsor_lines.db_services import SponsorLineServiceDB

    return SponsorLineServiceDB(database)


def _sponsor_sponsor_line_factory(database: Database) -> BaseServiceDB:
    from src.sponsor_sponsor_line_connection.db_services import SponsorSponsorLineServiceDB

    return SponsorSponsorLineServiceDB(database)


def _matchdata_factory(database: Database) -> BaseServiceDB:
    from src.matchdata.db_services import MatchDataServiceDB

    return MatchDataServiceDB(database)


def _playclock_factory(database: Database) -> BaseServiceDB:
    from src.playclocks.db_services import PlayClockServiceDB

    return PlayClockServiceDB(database)


def _gameclock_factory(database: Database) -> BaseServiceDB:
    from src.gameclocks.db_services import GameClockServiceDB

    return GameClockServiceDB(database)


def _scoreboard_factory(database: Database) -> BaseServiceDB:
    from src.scoreboards.db_services import ScoreboardServiceDB

    return ScoreboardServiceDB(database)


def _football_event_factory(database: Database) -> BaseServiceDB:
    from src.football_events.db_services import FootballEventServiceDB

    return FootballEventServiceDB(database)


def _match_stats_factory(database: Database) -> BaseServiceDB:
    from src.matches.stats_service import MatchStatsServiceDB

    return MatchStatsServiceDB(database)


def _match_data_cache_factory(database: Database) -> Any:
    from src.matches.match_data_cache_service import MatchDataCacheService

    return MatchDataCacheService(database)


def _user_factory(database: Database) -> BaseServiceDB:
    from src.users.db_services import UserServiceDB

    return UserServiceDB(database)


def _global_setting_factory(database: Database) -> BaseServiceDB:
    from src.global_settings.db_services import GlobalSettingServiceDB

    return GlobalSettingServiceDB(database)


def _role_factory(database: Database) -> BaseServiceDB:
    from src.roles.db_services import RoleServiceDB

    return RoleServiceDB(database)


def register_all_services(database: Database) -> ServiceRegistry:
    """Register all service factories with the global registry.

    This function should be called during application startup to ensure
    all services are available for dependency injection.

    Args:
        database: Database instance for service initialization

    Returns:
        Initialized ServiceRegistry instance
    """
    registry = get_service_registry()

    services: tuple[ServiceDefinition, ...] = (
        ("sport", _sport_factory, False),
        ("season", _season_factory, False),
        ("tournament", _tournament_factory, False),
        ("team", _team_factory, False),
        ("team_tournament", _team_tournament_factory, False),
        ("match", _match_factory, False),
        ("player", _player_factory, False),
        ("person", _person_factory, False),
        ("player_match", _player_match_factory, False),
        ("player_team_tournament", _player_team_tournament_factory, False),
        ("position", _position_factory, False),
        ("sponsor", _sponsor_factory, False),
        ("sponsor_line", _sponsor_line_factory, False),
        ("sponsor_sponsor_line", _sponsor_sponsor_line_factory, False),
        ("matchdata", _matchdata_factory, False),
        ("playclock", _playclock_factory, True),
        ("gameclock", _gameclock_factory, True),
        ("scoreboard", _scoreboard_factory, False),
        ("football_event", _football_event_factory, False),
        ("match_stats", _match_stats_factory, False),
        ("match_data_cache", _match_data_cache_factory, True),
        ("user", _user_factory, False),
        ("global_setting", _global_setting_factory, False),
        ("role", _role_factory, False),
    )

    for service_name, factory, singleton in services:
        if not registry.has(service_name):
            register_service(service_name, factory, singleton=singleton)

    return registry
