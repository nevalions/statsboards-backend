# Router Registry System

## Overview

The Router Registry system provides a centralized, configuration-based approach to managing FastAPI routers from domain modules. This eliminates the need for manual imports and registration in `main.py`, making the codebase more maintainable and scalable.

## Architecture

### Components

1. **RouterConfig** (`src/core/router_registry.py`): Pydantic model representing a single router configuration
2. **RouterRegistry** (`src/core/router_registry.py`): Main registry class for managing routers
3. **configure_routers()** (`src/core/router_registry.py`): Configuration function that registers all routers with priorities

## Features

- **Configuration-based Registration**: All routers are configured in one central location
- **Priority-based Ordering**: Routers are registered in priority order (lower numbers first)
- **Enable/Disable Routers**: Individual routers can be easily disabled without code changes
- **Auto-discovery Support**: Built-in support for discovering routers from domain modules
- **Plugin-like Architecture**: New domain modules can be added with minimal changes to main.py

## Usage

### Adding a New Router

When creating a new domain module with a router:

1. Create your domain module following the standard structure:
   ```
   src/my_domain/
       __init__.py      # Exports router
       db_services.py   # Service layer
       schemas.py       # Pydantic schemas
       views.py         # Router definition
   ```

2. In `views.py`, define your router:
   ```python
   from fastapi import APIRouter

   api_my_domain_router = APIRouter(prefix="/api/my-domain", tags=["my-domain"])

   @api_my_domain_router.get("/")
   async def get_items():
       return {"items": []}
   ```

3. In `__init__.py`, export the router:
   ```python
   from .views import api_my_domain_router
   ```

4. Add configuration in `src/core/router_registry.py`:
   ```python
   def configure_routers(registry: RouterRegistry) -> RouterRegistry:
       # ... existing routers ...
       registry.register_router(
           "src.my_domain",
           "api_my_domain_router",
           enabled=True,
           priority=999,
       )
       return registry
   ```

### Disabling a Router

To temporarily disable a router without removing code:

```python
registry.register_router(
    "src.some_domain",
    "api_some_router",
    enabled=False,  # Set to False to disable
    priority=100,
)
```

### Changing Router Order

Routers are registered in priority order (lower numbers first). To change the order:

```python
# Register important routers first
registry.register_router("src.sports", "api_sport_router", priority=10)
registry.register_router("src.teams", "api_team_router", priority=20)
```

## Current Router Configuration

The following routers are currently registered (ordered by priority):

| Priority | Module | Router |
|----------|--------|--------|
| 5 | src.global_settings | api_global_setting_router |
| 10 | src.sports | api_sport_router |
| 20 | src.seasons | api_season_router |
| 30 | src.tournaments | api_tournament_router |
| 40 | src.teams | api_team_router |
| 50 | src.team_tournament | api_team_tournament_router |
| 60 | src.matches | api_match_crud_router |
| 61 | src.matches | api_match_websocket_router |
| 62 | src.matches | api_match_parser_router |
| 70 | src.matchdata | api_matchdata_router |
| 80 | src.playclocks | api_playclock_router |
| 81 | src.gameclocks | api_gameclock_router |
| 90 | src.scoreboards | api_scoreboards_router |
| 100 | src.sponsors | api_sponsor_router |
| 101 | src.sponsor_lines | api_sponsor_line_router |
| 102 | src.sponsor_sponsor_line_connection | api_sponsor_sponsor_line_router |
| 110 | src.person | api_person_router |
| 120 | src.player | api_player_router |
| 130 | src.player_team_tournament | api_player_team_tournament_router |
| 140 | src.positions | api_position_router |
| 150 | src.player_match | api_player_match_router |
| 160 | src.football_events | api_football_event_router |
| 190 | src.auth | api_auth_router |
| 200 | src.users | api_user_router |
| 201 | src.roles | api_role_router |

## Migration Notes

### Before (Old System)

```python
# main.py
from src.sports import api_sport_router
from src.teams import api_team_router
from src.players import api_player_router
# ... many more imports ...

app.include_router(api_sport_router)
app.include_router(api_team_router)
app.include_router(api_player_router)
# ... many more registrations ...
```

### After (Router Registry)

```python
# main.py
from src.core.router_registry import RouterRegistry, configure_routers

registry = configure_routers(RouterRegistry())
registry.register_all(app)
```

All router configuration is centralized in `src/core/router_registry.py`.

## Benefits

1. **Maintainability**: All router configurations in one place
2. **Scalability**: Easy to add/remove routers
3. **Flexibility**: Enable/disable routers without code removal
4. **Order Control**: Priority-based router ordering
5. **Plugin Architecture**: New modules integrate seamlessly
6. **Reduced Imports**: Cleaner main.py with fewer direct imports
7. **Better Testing**: Easier to test router registration logic

## Auto-discovery (Optional)

The registry includes an `discover_routers()` method that can automatically scan domain modules for routers:

```python
registry = RouterRegistry()
registry.discover_routers()  # Automatically find all api_*_router instances
registry.register_all(app)
```

Note: Auto-discovery is currently not used in favor of explicit configuration for better control over router ordering and enabling/disabling.
