"""FastAPI test app fixtures with configurable router groups.

This module provides factory functions and fixtures for creating FastAPI test
applications with minimal router sets, improving test performance by only
initializing required routers.
"""

from typing import Literal

from fastapi import FastAPI

# Router group definitions
RouterGroup = Literal["core", "sport", "player", "match", "sponsor", "all"]

CORE_ROUTERS: list[RouterGroup] = ["core"]
SPORT_ROUTERS: list[RouterGroup] = ["core", "sport"]
PLAYER_ROUTERS: list[RouterGroup] = ["core", "player"]
MATCH_ROUTERS: list[RouterGroup] = ["core", "match"]
SPONSOR_ROUTERS: list[RouterGroup] = ["core", "sponsor"]
ALL_ROUTERS: list[RouterGroup] = ["all"]


def create_test_app(
    router_groups: list[RouterGroup] | None = None,
) -> FastAPI:
    """Create FastAPI app with specified router groups.

    Args:
        router_groups: List of router group names to include. If None or ["all"],
            includes all routers. Available groups: "core", "sport", "player",
            "match", "sponsor", "all".

    Returns:
        FastAPI application instance with configured routers.

    Example:
        >>> # Minimal app with only core routers
        >>> app = create_test_app(["core"])

        >>> # Sport-related routers
        >>> app = create_test_app(["core", "sport"])

        >>> # All routers (default)
        >>> app = create_test_app()  # or create_test_app(["all"])
    """
    from src.auth.views import api_auth_router
    from src.core import health
    from src.football_events.views import FootballEventAPIRouter
    from src.gameclocks.views import GameClockAPIRouter
    from src.global_settings.views import GlobalSettingAPIRouter
    from src.matchdata.views import MatchDataAPIRouter
    from src.matches.crud_router import MatchCRUDRouter
    from src.matches.parser_router import MatchParserRouter
    from src.matches.websocket_router import MatchWebSocketRouter
    from src.person.views import PersonAPIRouter
    from src.playclocks.views import PlayClockAPIRouter
    from src.player.views import PlayerAPIRouter
    from src.player_match.views import PlayerMatchAPIRouter
    from src.player_team_tournament.views import PlayerTeamTournamentAPIRouter
    from src.positions.views import PositionAPIRouter
    from src.roles.views import RoleAPIRouter
    from src.scoreboards.views import ScoreboardAPIRouter
    from src.seasons.views import SeasonAPIRouter
    from src.sponsor_lines.views import SponsorLineAPIRouter
    from src.sponsor_sponsor_line_connection.views import SponsorSponsorLineAPIRouter
    from src.sponsors.views import SponsorAPIRouter
    from src.sports.views import SportAPIRouter
    from src.team_tournament.views import TeamTournamentRouter
    from src.teams.views import TeamAPIRouter
    from src.tournaments.views import TournamentAPIRouter
    from src.users.views import get_user_router

    if router_groups is None:
        router_groups = ["all"]

    app = FastAPI()

    # Always include if "all" is requested
    include_all = "all" in router_groups

    # Core routers
    if include_all or "core" in router_groups:
        app.include_router(health.router)
        app.include_router(api_auth_router)
        app.include_router(GlobalSettingAPIRouter().route())
        app.include_router(get_user_router())

        try:
            role_router = RoleAPIRouter(None, service_name="role").route()
            app.include_router(role_router)
        except Exception:
            pass  # Role router may fail to initialize in test environment

    # Sport-related routers
    if include_all or "sport" in router_groups:
        app.include_router(SportAPIRouter().route())
        app.include_router(TeamAPIRouter().route())
        app.include_router(TournamentAPIRouter(None, service_name="tournament").route())
        app.include_router(SeasonAPIRouter().route())
        app.include_router(TeamTournamentRouter(None, service_name="team_tournament").route())

    # Player-related routers
    if include_all or "player" in router_groups:
        app.include_router(PlayerAPIRouter(None, service_name="player").route())
        app.include_router(PersonAPIRouter().route())
        app.include_router(PositionAPIRouter().route())
        app.include_router(PlayerMatchAPIRouter(None, service_name="player_match").route())
        app.include_router(
            PlayerTeamTournamentAPIRouter(None, service_name="player_team_tournament").route()
        )

    # Match-related routers
    if include_all or "match" in router_groups:
        app.include_router(MatchCRUDRouter(None, service_name="match").route())
        app.include_router(MatchWebSocketRouter(None, service_name="match").route())
        app.include_router(MatchParserRouter(None, service_name="match").route())
        app.include_router(MatchDataAPIRouter().route())
        app.include_router(GameClockAPIRouter().route())
        app.include_router(PlayClockAPIRouter(None, service_name="playclock").route())
        app.include_router(ScoreboardAPIRouter(None, service_name="scoreboard").route())
        app.include_router(FootballEventAPIRouter().route())

    # Sponsor-related routers
    if include_all or "sponsor" in router_groups:
        app.include_router(SponsorAPIRouter().route())
        app.include_router(SponsorLineAPIRouter(None, service_name="sponsor_line").route())
        app.include_router(
            SponsorSponsorLineAPIRouter(None, service_name="sponsor_sponsor_line").route()
        )

    return app
