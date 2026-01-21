# Service Layer Decoupling

## Overview

This document describes the service layer decoupling implementation that addresses the issue of services directly importing and depending on each other.

## Problem

Previously, services were tightly coupled through direct imports:

```python
# matches/db_services.py (BEFORE)
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB

class MatchServiceDB(BaseServiceDB):
    async def get_sport_by_match_id(self, match_id: int):
        tournament_service = TournamentServiceDB(self.db)  # Direct instantiation
        sport_service = SportServiceDB(self.db)  # Direct instantiation
        # ...
```

This created several issues:
- Tight coupling between services
- Difficult to test in isolation
- Hard to swap implementations
- Circular import dependencies

## Solution: Service Registry with Dependency Injection

### Architecture

The solution implements a Service Registry pattern with dependency injection:

1. **ServiceRegistry** (`src/core/service_registry.py`):
   - Central registry for all service factories
   - Supports both transient and singleton instances
   - Lazy initialization to avoid early access issues

2. **Service Initialization** (`src/core/service_initialization.py`):
   - Registers all services during application startup
   - Provides a single source of truth for service configuration

3. **Lazy Service Access**:
   - Services access the registry through a property
   - Registry is only initialized when first accessed
   - Avoids initialization order issues

### Implementation

#### 1. Service Registry

```python
# src/core/service_registry.py

class ServiceRegistry:
    def __init__(self, database: Database):
        self.database = database
        self._services: dict[str, Callable[[], Any]] = {}
        self._singletons: dict[str, Any] = {}

    def register(self, service_name: str, factory: Callable[..., T], singleton: bool = False):
        """Register a service factory."""
        self._services[service_name] = factory

    def get(self, service_name: str) -> T:
        """Get a new service instance."""
        factory = self._services[service_name]
        return factory(self.database)

    def get_singleton(self, service_name: str) -> T:
        """Get a cached singleton instance."""
        if service_name not in self._singletons:
            self._singletons[service_name] = self._services[service_name](self.database)
        return self._singletons[service_name]
```

#### 2. Service Initialization

```python
# src/core/service_initialization.py

def register_all_services(database: Database) -> ServiceRegistry:
    """Register all service factories."""
    registry = get_service_registry()

    # Register all services
    from src.sports.db_services import SportServiceDB
    register_service("sport", lambda db: SportServiceDB(db), singleton=False)

    from src.teams.db_services import TeamServiceDB
    register_service("team", lambda db: TeamServiceDB(db), singleton=False)

    # ... more services
    return registry
```

#### 3. Usage in Services

```python
# matches/db_services.py (AFTER)

class MatchServiceDB(BaseServiceDB):
    def __init__(self, database: Database):
        super().__init__(database, MatchDB)
        self._service_registry = None

    @property
    def service_registry(self):
        """Lazy initialization of service registry."""
        if self._service_registry is None:
            self._service_registry = get_service_registry()
        return self._service_registry

    async def get_sport_by_match_id(self, match_id: int):
        tournament_service = self.service_registry.get("tournament")
        sport_service = self.service_registry.get("sport")
        # ...
```

#### 4. Application Startup

```python
# src/main.py

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan with service registry initialization."""
    try:
        # Initialize service registry before any services are used
        init_service_registry(db)
        register_all_services(db)
        logger.info("Service registry initialized")

        await db.test_connection()
        yield
    except Exception as e:
        db_logger.critical(f"Critical error during startup: {e}", exc_info=True)
        raise
    finally:
        await db.close()
```

## Usage in Router Endpoints

When creating router endpoints that need database access, especially for operations that create their own sessions (like `get_value()` calls that use `async with self.db.async_session()`), use the service registry to ensure the correct database connection is used:

```python
# src/my_module/views.py

from src.core.service_registry import get_service_registry

class MyAPIRouter(BaseRouter):
    def route(self):
        router = super().route()

        @router.get("/value/{key}")
        async def get_value_endpoint(key: str):
            # Get fresh service instance with correct database for current event loop
            registry = get_service_registry()
            service = registry.get("my_service")
            return await service.get_value(key)

        @router.get("/complex-operation/{id}")
        async def complex_operation_endpoint(id: int):
            # Get database from registry for multiple service instantiation
            registry = get_service_registry()
            database = registry.database

            service_a = ServiceA(database)
            service_b = ServiceB(database)
            # ... use services
```

### Why This Matters

The global `db` object is created at module load time and bound to the initial event loop. During parallel test execution (with pytest-xdist), different test workers run in different event loops. Using the global `db` directly in endpoints can cause "Task got Future attached to a different loop" errors.

By using `get_service_registry().database`, you get the database instance that was registered during application/test startup for the current event loop context.

### When to Use the Registry in Endpoints

Use the service registry pattern when:
1. The endpoint needs to create new service instances dynamically
2. The endpoint calls service methods that create their own sessions
3. The router is created at module load time with a global `db` reference

The router initialization itself can still use the global `db`:
```python
# This is fine - router is re-initialized per test
api_router = MyAPIRouter(MyServiceDB(db)).route()
```

But endpoint code should use the registry for runtime database access.

## Benefits

1. **Loose Coupling**: Services no longer directly import each other
2. **Testability**: Easy to mock dependencies in tests
3. **Flexibility**: Easy to swap implementations or add interceptors
4. **Centralized Configuration**: All service registration in one place
5. **Lazy Initialization**: Registry only accessed when needed
6. **No Circular Imports**: Dependencies resolved through names, not imports
7. **Event Loop Safety**: Registry ensures correct database for current async context

## Migration Guide

### For Existing Services

To update an existing service to use the registry:

1. **Remove direct imports**:
   ```python
   # BEFORE
   from src.teams.db_services import TeamServiceDB

   # AFTER
   # No import needed
   ```

2. **Add lazy registry access**:
   ```python
   class MyService(BaseServiceDB):
       def __init__(self, database: Database):
           super().__init__(database, MyModel)
           self._service_registry = None

       @property
       def service_registry(self):
           if self._service_registry is None:
               from src.core.service_registry import get_service_registry
               self._service_registry = get_service_registry()
           return self._service_registry
   ```

3. **Use registry to get dependencies**:
   ```python
   # BEFORE
   team_service = TeamServiceDB(self.db)

   # AFTER
   team_service = self.service_registry.get("team")
   ```

### For New Services

When creating a new service:

1. Create the service class as usual
2. Register it in `src/core/service_initialization.py`:
   ```python
   from src.my_new_service.db_services import MyNewServiceDB
   register_service("my_new_service", lambda db: MyNewServiceDB(db), singleton=False)
   ```
3. Use the service name to access it from other services

## Testing

Services are initialized with the service registry in test fixtures:

```python
# tests/conftest.py

@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Database fixture that ensures a clean state using transactions."""
    database = Database(db_url_str, echo=False)

    # Initialize service registry for each test
    init_service_registry(database)
    register_all_services(database)

    # Create tables and run tests
    # ...

    yield database
```

## Event-Driven Architecture (Future Enhancement)

For truly decoupled cross-domain operations, consider implementing event-driven architecture:

### Current State

Services still call each other directly (through registry):
```python
# MatchService directly calls TeamService
team_service = self.service_registry.get("team")
team = await team_service.get_by_id(team_id)
```

### Future: Event-Driven

Services emit events and subscribers react:

```python
# MatchService emits event
class MatchServiceDB(BaseServiceDB):
    async def create_match(self, match_data):
        match = await self.create(match_data)
        await event_bus.emit("match.created", match_id=match.id)
        return match

# TeamService subscribes to events
@event_bus.subscribe("match.created")
async def on_match_created(match_id):
    # Update team statistics, etc.
    pass
```

Benefits:
- Complete decoupling
- Asynchronous processing
- Easy to add side effects
- Better scalability

### Implementation Considerations

- Use existing WebSocket infrastructure
- Add Redis pub/sub for distributed events
- Event replay support for debugging
- Event versioning for schema evolution

## Service Names

Current registered service names:

- `sport`
- `season`
- `tournament`
- `team`
- `match`
- `player`
- `person`
- `player_match`
- `player_team_tournament`
- `position`
- `sponsor`
- `sponsor_line`
- `sponsor_sponsor_line`
- `matchdata`
- `playclock`
- `gameclock`
- `scoreboard`
- `football_event`
- `match_stats`
- `match_data_cache` (singleton)
- `user`
- `global_setting`

Use these names when accessing services through registry.
