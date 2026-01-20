"""Service initialization and registration module.

This module handles the registration of all service factories with the
global service registry, enabling dependency injection and decoupling
services from each other.
"""

from src.core.models.base import Database
from src.core.service_registry import (
    ServiceRegistry,
    get_service_registry,
    register_service,
)


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

    if not registry.has("sport"):
        from src.sports.db_services import SportServiceDB

        register_service("sport", lambda db: SportServiceDB(db), singleton=False)

    if not registry.has("season"):
        from src.seasons.db_services import SeasonServiceDB

        register_service("season", lambda db: SeasonServiceDB(db), singleton=False)

    if not registry.has("tournament"):
        from src.tournaments.db_services import TournamentServiceDB

        register_service("tournament", lambda db: TournamentServiceDB(db), singleton=False)

    if not registry.has("team"):
        from src.teams.db_services import TeamServiceDB

        register_service("team", lambda db: TeamServiceDB(db), singleton=False)

    if not registry.has("match"):
        from src.matches.db_services import MatchServiceDB

        register_service("match", lambda db: MatchServiceDB(db), singleton=False)

    if not registry.has("player"):
        from src.player.db_services import PlayerServiceDB

        register_service("player", lambda db: PlayerServiceDB(db), singleton=False)

    if not registry.has("person"):
        from src.person.db_services import PersonServiceDB

        register_service("person", lambda db: PersonServiceDB(db), singleton=False)

    if not registry.has("player_match"):
        from src.player_match.db_services import PlayerMatchServiceDB

        register_service("player_match", lambda db: PlayerMatchServiceDB(db), singleton=False)

    if not registry.has("player_team_tournament"):
        from src.player_team_tournament.db_services import PlayerTeamTournamentServiceDB

        register_service(
            "player_team_tournament", lambda db: PlayerTeamTournamentServiceDB(db), singleton=False
        )

    if not registry.has("position"):
        from src.positions.db_services import PositionServiceDB

        register_service("position", lambda db: PositionServiceDB(db), singleton=False)

    if not registry.has("sponsor"):
        from src.sponsors.db_services import SponsorServiceDB

        register_service("sponsor", lambda db: SponsorServiceDB(db), singleton=False)

    if not registry.has("sponsor_line"):
        from src.sponsor_lines.db_services import SponsorLineServiceDB

        register_service("sponsor_line", lambda db: SponsorLineServiceDB(db), singleton=False)

    if not registry.has("sponsor_sponsor_line"):
        from src.sponsor_sponsor_line_connection.db_services import SponsorSponsorLineServiceDB

        register_service(
            "sponsor_sponsor_line", lambda db: SponsorSponsorLineServiceDB(db), singleton=False
        )

    if not registry.has("matchdata"):
        from src.matchdata.db_services import MatchDataServiceDB

        register_service("matchdata", lambda db: MatchDataServiceDB(db), singleton=False)

    if not registry.has("playclock"):
        from src.playclocks.db_services import PlayClockServiceDB

        register_service("playclock", lambda db: PlayClockServiceDB(db), singleton=False)

    if not registry.has("gameclock"):
        from src.gameclocks.db_services import GameClockServiceDB

        register_service("gameclock", lambda db: GameClockServiceDB(db), singleton=False)

    if not registry.has("scoreboard"):
        from src.scoreboards.db_services import ScoreboardServiceDB

        register_service("scoreboard", lambda db: ScoreboardServiceDB(db), singleton=False)

    if not registry.has("football_event"):
        from src.football_events.db_services import FootballEventServiceDB

        register_service("football_event", lambda db: FootballEventServiceDB(db), singleton=False)

    if not registry.has("match_stats"):
        from src.matches.stats_service import MatchStatsServiceDB

        register_service("match_stats", lambda db: MatchStatsServiceDB(db), singleton=False)

    if not registry.has("match_data_cache"):
        from src.matches.match_data_cache_service import MatchDataCacheService

        register_service("match_data_cache", lambda db: MatchDataCacheService(db), singleton=True)

    if not registry.has("user"):
        from src.users.db_services import UserServiceDB

        register_service("user", lambda db: UserServiceDB(db), singleton=False)

    if not registry.has("global_setting"):
        from src.global_settings.db_services import GlobalSettingServiceDB

        register_service("global_setting", lambda db: GlobalSettingServiceDB(db), singleton=False)

    return registry
