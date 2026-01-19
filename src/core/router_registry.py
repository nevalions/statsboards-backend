import importlib
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

logger = logging.getLogger("backend_logger_router_registry")


class RouterConfig(BaseModel):
    """Configuration for a single router."""

    module_path: str
    router_name: str
    enabled: bool = True
    priority: int = 100

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, RouterConfig):
            return NotImplemented
        return self.priority < other.priority


class RouterRegistry:
    """Registry for managing and auto-discovering routers from domain modules."""

    def __init__(self, src_path: Path | None = None):
        self.src_path = src_path or Path(__file__).parent.parent
        self._routers: list[RouterConfig] = []
        self._loaded_routers: dict[str, APIRouter] = {}

    def register_router(
        self,
        module_path: str,
        router_name: str,
        enabled: bool = True,
        priority: int = 100,
    ) -> None:
        config = RouterConfig(
            module_path=module_path,
            router_name=router_name,
            enabled=enabled,
            priority=priority,
        )
        self._routers.append(config)
        logger.debug(
            f"Registered router config: {module_path}.{router_name} "
            f"(enabled={enabled}, priority={priority})"
        )

    def discover_routers(self, domain_package: str = "src") -> None:
        """Auto-discover routers from domain modules."""
        src_dir = self.src_path / domain_package

        if not src_dir.exists():
            logger.warning(f"Source directory not found: {src_dir}")
            return

        for module_dir in src_dir.iterdir():
            if not module_dir.is_dir() or module_dir.name.startswith("_"):
                continue

            init_file = module_dir / "__init__.py"
            if not init_file.exists():
                continue

            try:
                module = importlib.import_module(f"{domain_package}.{module_dir.name}")

                for attr_name in dir(module):
                    if attr_name.endswith("_router") and attr_name.startswith("api_"):
                        router = getattr(module, attr_name)
                        if isinstance(router, APIRouter):
                            self.register_router(
                                module_path=f"{domain_package}.{module_dir.name}",
                                router_name=attr_name,
                                enabled=True,
                                priority=100,
                            )
                            logger.info(f"Auto-discovered router: {module_dir.name}.{attr_name}")
            except Exception as e:
                logger.error(
                    f"Failed to discover routers in {module_dir.name}: {e}",
                    exc_info=True,
                )

    def load_router(self, config: RouterConfig) -> APIRouter:
        if config.router_name in self._loaded_routers:
            return self._loaded_routers[config.router_name]

        try:
            module = importlib.import_module(config.module_path)
            router = getattr(module, config.router_name)
            if not isinstance(router, APIRouter):
                raise TypeError(f"Expected APIRouter, got {type(router)} for {config.router_name}")
            self._loaded_routers[config.router_name] = router
            logger.debug(f"Loaded router: {config.module_path}.{config.router_name}")
            return router
        except Exception as e:
            logger.error(
                f"Failed to load router {config.module_path}.{config.router_name}: {e}",
                exc_info=True,
            )
            raise

    def register_all(self, app: FastAPI) -> None:
        """Register all enabled routers with the FastAPI app."""
        sorted_configs = sorted(self._routers)

        for config in sorted_configs:
            if not config.enabled:
                logger.info(f"Skipping disabled router: {config.router_name}")
                continue

            try:
                router = self.load_router(config)
                app.include_router(router)
                logger.info(f"Included router: {config.router_name}")
            except Exception as e:
                logger.error(
                    f"Failed to include router {config.router_name}: {e}",
                    exc_info=True,
                )

    def get_router_configs(self) -> list[RouterConfig]:
        return self._routers.copy()


def configure_routers(registry: RouterRegistry) -> RouterRegistry:
    """Configure router registration with custom priorities and ordering."""

    registry.register_router("src.global_settings", "api_global_setting_router", priority=5)
    registry.register_router("src.sports", "api_sport_router", priority=10)
    registry.register_router("src.seasons", "api_season_router", priority=20)
    registry.register_router("src.tournaments", "api_tournament_router", priority=30)
    # registry.register_router(
    #     "src.tournaments", "template_tournament_router", priority=31
    # )
    registry.register_router("src.teams", "api_team_router", priority=40)
    registry.register_router("src.team_tournament", "api_team_tournament_router", priority=50)
    registry.register_router("src.matches", "api_match_crud_router", priority=60)
    registry.register_router("src.matches", "api_match_websocket_router", priority=61)
    registry.register_router("src.matches", "api_match_parser_router", priority=62)
    # registry.register_router("src.matches", "template_match_router", priority=63)
    registry.register_router("src.matchdata", "api_matchdata_router", priority=70)
    registry.register_router("src.playclocks", "api_playclock_router", priority=80)
    registry.register_router("src.gameclocks", "api_gameclock_router", priority=81)
    registry.register_router("src.scoreboards", "api_scoreboards_router", priority=90)
    registry.register_router("src.sponsors", "api_sponsor_router", priority=100)
    registry.register_router("src.sponsor_lines", "api_sponsor_line_router", priority=101)
    registry.register_router(
        "src.sponsor_sponsor_line_connection",
        "api_sponsor_sponsor_line_router",
        priority=102,
    )
    registry.register_router("src.person", "api_person_router", priority=110)
    registry.register_router("src.player", "api_player_router", priority=120)
    registry.register_router(
        "src.player_team_tournament",
        "api_player_team_tournament_router",
        priority=130,
    )
    registry.register_router("src.positions", "api_position_router", priority=140)
    registry.register_router("src.player_match", "api_player_match_router", priority=150)
    registry.register_router("src.football_events", "api_football_event_router", priority=160)
    registry.register_router("src.auth", "api_auth_router", priority=190)
    registry.register_router("src.users", "api_user_router", priority=200)
    registry.register_router("src.roles", "api_role_router", priority=201)

    return registry
