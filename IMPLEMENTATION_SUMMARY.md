# Service Layer Decoupling - Implementation Summary

## What Was Implemented

This implementation addresses the service layer coupling issue where services were directly importing and instantiating other services, creating tight coupling and making testing difficult.

## Changes Made

### 1. Created Service Registry (`src/core/service_registry.py`)

A central registry for managing service instances with dependency injection support:

- `ServiceRegistry` class: Core registry implementation
- `register()`: Register service factories with optional singleton support
- `get()`: Get new service instances
- `get_singleton()`: Get cached singleton instances
- Global functions: `init_service_registry()`, `get_service_registry()`, `get_service()`

**Key Features:**
- Lazy initialization to avoid early access issues
- Support for both transient and singleton services
- Type-safe service access through TypeVar
- Global registry access for convenience

### 2. Created Service Initialization (`src/core/service_initialization.py`)

Centralized service registration during application startup:

- `register_all_services()`: Registers all domain services
- Registers 18 services with descriptive names
- Uses lambda factories for deferred instantiation

**Registered Services:**
- sport, season, tournament, team, match
- player, person, player_match, player_team_tournament
- position, sponsor, sponsor_line, sponsor_sponsor_line
- matchdata, playclock, gameclock, scoreboard, football_event

### 3. Updated Services to Use Registry

#### Matches Service (`src/matches/db_services.py`)

**Before:**
```python
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB

class MatchServiceDB(BaseServiceDB):
    async def get_sport_by_match_id(self, match_id: int):
        tournament_service = TournamentServiceDB(self.db)  # Direct instantiation
        sport_service = SportServiceDB(self.db)  # Direct instantiation
```

**After:**
```python
from src.core.service_registry import get_service_registry

class MatchServiceDB(BaseServiceDB):
    def __init__(self, database: Database):
        super().__init__(database, MatchDB)
        self._service_registry = None

    @property
    def service_registry(self):
        if self._service_registry is None:
            self._service_registry = get_service_registry()
        return self._service_registry

    async def get_sport_by_match_id(self, match_id: int):
        tournament_service = self.service_registry.get("tournament")
        sport_service = self.service_registry.get("sport")
```

#### Matches Router (`src/matches/crud_router.py`)

Updated all endpoints that instantiated services directly to use registry:
- `create_match_with_full_data_endpoint`
- `get_sponsor_line_by_match_id_endpoint`
- `create_match_with_full_data_and_scoreboard_endpoint`

#### Player Match Service (`src/player_match/db_services.py`)

Updated methods that used other services:
- `get_player_in_sport()`: Uses `player_team_tournament` service
- `get_player_person_in_match()`: Uses `player` service
- `get_player_in_match_full_data()`: Uses `position` service

### 4. Updated Application Startup (`src/main.py`)

Added service registry initialization to lifespan manager:

```python
@asynccontextmanager
async def lifespan(_app: FastAPI):
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

### 5. Updated Test Configuration (`tests/conftest.py`)

Added service registry initialization to test_db fixture:

```python
@pytest_asyncio.fixture(scope="function")
async def test_db():
    database = Database(db_url_str, echo=False)

    # Initialize service registry for each test
    init_service_registry(database)
    register_all_services(database)

    # Create tables and run tests
    # ...
```

## Benefits Achieved

1. **Loose Coupling**: Services no longer directly import each other
2. **Testability**: Services can be easily mocked in tests
3. **Flexibility**: Easy to swap implementations or add interceptors
4. **Centralized Configuration**: All service registration in one place
5. **Lazy Initialization**: Registry only accessed when needed
6. **No Circular Imports**: Dependencies resolved through names, not imports
7. **Backward Compatible**: Existing tests continue to pass (123/123 tests passing)

## Files Changed

### New Files
- `src/core/service_registry.py` - Service registry implementation
- `src/core/service_initialization.py` - Service registration
- `SERVICE_LAYER_DECOUPLING.md` - Full documentation

### Modified Files
- `src/matches/db_services.py` - Updated to use registry
- `src/matches/crud_router.py` - Updated to use registry
- `src/player_match/db_services.py` - Updated to use registry
- `src/main.py` - Initialize registry on startup
- `tests/conftest.py` - Initialize registry in tests
- `AGENTS.md` - Added service registry guidance

## Testing

All existing tests continue to pass:
```bash
pytest tests/test_db_services/
# Result: 123 passed in 9.33s
```

Specific test results:
- Match service tests: 5/5 passed
- Player match service tests: 4/4 passed
- All service tests: 123/123 passed

## Future Enhancements

### Event-Driven Architecture

For even greater decoupling, consider implementing event-driven architecture:

**Current State:** Services call each other through registry (synchronous)
**Future:** Services emit events and subscribers react (asynchronous)

**Implementation Path:**
1. Create event bus service
2. Define event schemas
3. Add event emission to service methods
4. Create event subscribers for side effects
5. Use Redis pub/sub for distributed events

**Benefits:**
- Complete decoupling (no direct calls between services)
- Asynchronous processing
- Easy to add side effects
- Better scalability
- Event replay for debugging

See `SERVICE_LAYER_DECOUPLING.md` for detailed event-driven architecture guidance.

## Migration Guide

### For Existing Services

To update an existing service to use registry:

1. Remove direct imports of other services
2. Add lazy registry access property
3. Replace direct instantiation with registry access
4. Update test fixtures if needed

### For New Services

When creating a new service:

1. Create service class as usual
2. Register in `src/core/service_initialization.py`
3. Use service name to access from other services

## Conclusion

The service layer decoupling implementation successfully addresses the original issue while maintaining backward compatibility and passing all existing tests. The registry pattern provides a clean, testable architecture that can be extended with event-driven architecture in the future.
