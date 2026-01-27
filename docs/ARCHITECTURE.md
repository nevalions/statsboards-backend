# Architecture Documentation

## Overview

The StatsBoards Backend is a FastAPI-based microservice designed for managing sports tournaments, matches, teams, and real-time game data across a variety of sports. The architecture follows a layered design with clear separation of concerns, dependency injection, and domain-driven design principles.

Currently supports:
- American football
- Flag football
- Extensible for additional sports

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Layer                         │
│  (Web Browsers, Mobile Apps, Third-party Integrations)      │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP/WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  - Router Registry System                                    │
│  - Request/Response Validation (Pydantic)                    │
│  - Global Exception Handlers                                │
│  - WebSocket Connection Management                          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer (Business Logic)              │
│  - Service Registry (Dependency Injection)                   │
│  - Domain Services (TeamService, MatchService, etc.)       │
│  - Cross-Service Communication via Registry                  │
│  - Business Logic & Validation                               │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Access Layer                          │
│  - BaseServiceDB (CRUD Mixins)                             │
│  - SQLAlchemy ORM                                            │
│  - Async Database Operations                                │
│  - Query Builders & Relationship Management                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database Layer                             │
│  - PostgreSQL (Production & Test)                            │
│  - Connection Pooling (asyncpg)                             │
│  - Transaction Management                                    │
│  - Alembic Migrations                                        │
└─────────────────────────────────────────────────────────────┘
```

## Core Architectural Patterns

### 1. Layered Architecture

The application follows a classic 3-tier architecture with additional concerns:

- **API Layer**: FastAPI routers handle HTTP requests, validate input, and return responses
- **Service Layer**: Business logic, validation, and orchestration of data operations
- **Data Access Layer**: Database operations, CRUD operations, and relationship management
- **Cross-Cutting Concerns**: Logging, exception handling, configuration, WebSocket management

### 2. Domain-Driven Design (DDD)

Each domain module (teams, matches, tournaments, etc.) is self-contained with:

- **Models**: SQLAlchemy database models with relationships
- **Schemas**: Pydantic models for request/response validation
- **Services**: Business logic and data operations
- **Views**: API endpoints (FastAPI routers)

```
src/
├── teams/                    # Domain: Team Management
│   ├── __init__.py
│   ├── db_services.py      # Service Layer
│   ├── schemas.py          # Request/Response Models
│   └── views.py            # API Endpoints
├── matches/                  # Domain: Match Management
├── tournaments/             # Domain: Tournament Management
└── [other domains...]
```

### 3. Service Registry Pattern

**Purpose**: Decouple services and enable dependency injection

**Implementation**:
- Centralized service registration in `src/core/service_initialization.py`
- Services accessed via `service_registry.get("service_name")`
- Lazy initialization to avoid circular dependencies
- Both transient and singleton support

**Benefits**:
- Loose coupling between services
- Easy to test with mocked dependencies
- Flexible for swapping implementations
- No circular import issues

**Example**:
```python
# Service accessing another service
class MatchServiceDB(BaseServiceDB):
    async def get_sport_by_match_id(self, match_id: int):
        tournament_service = self.service_registry.get("tournament")
        sport_service = self.service_registry.get("sport")
        # ...
```

**See**: `SERVICE_LAYER_DECOUPLING.md` for complete documentation

### 4. Router Registry Pattern

**Purpose**: Centralized router configuration and management

**Implementation**:
- All routers configured in `src/core/router_registry.py`
- Priority-based ordering (lower numbers first)
- Enable/disable routers without code changes
- Plugin-like architecture for new domains

**Benefits**:
- Single source of truth for router configuration
- Easy to add/remove routers
- Cleaner `main.py` with fewer imports
- Better testability

**Example**:
```python
# Register a router
registry.register_router(
    "src.teams",
    "api_team_router",
    enabled=True,
    priority=40,
)
```

**See**: `ROUTER_REGISTRY.md` for complete documentation

### 5. Base Router and Base Service Patterns

**BaseRouter**: Generic router with standard CRUD endpoints
- Inherit from `BaseRouter[SchemaType, CreateSchemaType, UpdateSchemaType]`
- Auto-generates GET /, GET /id/{id}, POST /, PUT /id/{id}
- Override or add custom endpoints as needed (including DELETE endpoints for authorization)

**BaseServiceDB**: Generic service with CRUD operations
- Inherit from `BaseServiceDB` and pass database model
- Provides create, get, get_all, update, delete operations
- Mixin-based architecture for flexible CRUD operations

**Benefits**:
- Consistent patterns across domains
- Reduced boilerplate code
- Easy to add new domains
- Type-safe operations

### 6. Mixin-Based Architecture

**Purpose**: Composable functionality for services and models

**Service Mixins** (`src/core/models/mixins/`):
- `CRUDMixin`: Standard CRUD operations (create, get, update, delete)
- `QueryMixin`: Advanced query operations (get_by_field, exists, count)
- `RelationshipMixin`: Relationship management (get_related_items, add_related_items)

**Model Mixins**:
- TimestampMixin: created_at and updated_at fields
- SoftDeleteMixin: deleted_at field for soft deletion
- CommonMixin: id and other common fields

**Benefits**:
- Reusable functionality across domains
- Single responsibility per mixin
- Easy to extend functionality
- DRY principle

### 7. Async/Await Throughout

**Purpose**: Non-blocking I/O for better performance

**Implementation**:
- All database operations use `async/await`
- Async SQLAlchemy with asyncpg driver
- Async context managers for sessions
- Async WebSocket connections

**Benefits**:
- Better performance under load
- Handles concurrent requests efficiently
- Non-blocking file operations
- Scalable real-time features

## Key Components

### Database Models (`src/core/models/`)

**Characteristics**:
- SQLAlchemy 2.0 async models
- Typed columns with `Mapped[type]` and `mapped_column()`
- Relationships with proper `back_populates`
- `TYPE_CHECKING` for forward references
- Mixin-based composition

**Example**:
```python
class TeamDB(Base, TimestampMixin, CommonMixin):
    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    eesl_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)

    # Relationships
    players: Mapped[list[PlayerDB]] = relationship(back_populates="team")
    tournaments: Mapped[list[TournamentDB]] = relationship(
        secondary="team_tournament", back_populates="teams"
    )
```

### Service Layer (`src/*/db_services.py`)

**Characteristics**:
- All services inherit from `BaseServiceDB`
- Use service registry for cross-service dependencies
- Structured logging with descriptive names
- Custom exception hierarchy
- Both decorator and manual error handling

**Error Handling Patterns**:
- **Preferred**: `@handle_service_exceptions` decorator for standard cases
- **Manual**: For complex error handling or special logic
- Specific exception types (ValidationError, NotFoundError, etc.)
- Appropriate HTTP status codes
- Structured logging with `exc_info=True`

**Example**:
```python
@handle_service_exceptions(item_name=ITEM, operation="creating")
async def create(self, item: TeamSchemaCreate) -> TeamDB:
    team = self.model(**item.model_dump())
    return await super().create(team)
```

### API Layer (`src/*/views.py`)

**Characteristics**:
- Inherit from `BaseRouter[SchemaType, CreateSchemaType, UpdateSchemaType]`
- Use descriptive endpoint names with `_endpoint` suffix
- Return `object.__dict__` for responses
- Custom endpoints added after `super().route()`

**Example**:
```python
class TeamAPIRouter(BaseRouter[TeamSchema, TeamSchemaCreate, TeamSchemaUpdate]):
    def __init__(self, service: TeamServiceDB):
        super().__init__("/api/teams", ["teams"], service)
        self.route()  # Standard CRUD endpoints

    async def create_team_endpoint(self, item: TeamSchemaCreate) -> dict:
        team = await self.service.create(item)
        return team.__dict__
```

### WebSocket Management (`src/websocket/`)

**Characteristics**:
- Connection manager for multiple client types
- Real-time data streaming for matches, scoreboards, gameclocks
- Background tasks for clock management and connection cleanup
- Redis pub/sub for scalable event distribution
- Automatic cleanup of stale connections (90-second timeout)

**Supported WebSocket Types**:
- Match data streaming
- Scoreboard updates
- Game clock synchronization
- Play clock updates

### WebSocket Message Architecture

#### Message Types

**Initial Connection Messages:**

| Message Type | Description | When Sent |
|--------------|-------------|------------|
| `initial-load` | Combined initial data with all match information | On new WebSocket connection |

**Ongoing Update Messages:**

| Message Type | Description | Trigger |
|--------------|-------------|----------|
| `match-update` | Match data, teams, scoreboard changes | Database NOTIF on match/teams/scoreboard |
| `gameclock-update` | Game clock time/status changes | Every second by ClockOrchestrator |
| `playclock-update` | Play clock time/status changes | Every second by ClockOrchestrator |
| `event-update` | Football events list | Database NOTIF on football events |
| `statistics-update` | Match statistics updates | Database NOTIF on match statistics |

#### Message Formats

**Initial Load Message:**

```typescript
{
  "type": "initial-load",
  "data": {
    "match": {
      "id": 123,
      "title": "Team A vs Team B",
      "match_date": "2026-01-21T19:00:00Z"
    },
    "teams_data": {
      "team_a": {
        "id": 1,
        "title": "Team A",
        "team_color": "#FF0000"
      },
      "team_b": {
        "id": 2,
        "title": "Team B",
        "team_color": "#0000FF"
      }
    },
    "scoreboard_data": {
      "id": 789,
      "match_id": 123,
      "team_a_game_color": "#FF0000",
      "team_b_game_color": "#0000FF"
    },
    "match_data": {
      "id": 456,
      "match_id": 123,
      "score_team_a": 14,
      "score_team_b": 10,
      "qtr": "1st"
    },
    "gameclock": {
      "id": 345,
      "match_id": 123,
      "gameclock": 720,
      "gameclock_status": "running"
    },
    "playclock": {
      "id": 234,
      "match_id": 123,
      "playclock": 40,
      "playclock_status": "running"
    },
    "events": [
      {
        "id": 1,
        "match_id": 123,
        "event_type": "touchdown"
      }
    ],
    "statistics": {
      "team_a": {
        "id": 1,
        "team_stats": {
          "offence_yards": 250,
          "pass_att": 20
        }
      },
      "team_b": {
        "id": 2,
        "team_stats": {
          "offence_yards": 200,
          "pass_att": 15
        }
      }
    },
    "server_time_ms": 1737648000050
  }
}
```

**Update Messages (format unchanged):**

```typescript
// gameclock-update
{
  "type": "gameclock-update",
  "match_id": 123,
  "gameclock": {
    "id": 345,
    "gameclock": 720,
    "gameclock_status": "running"
  }
}

// playclock-update
{
  "type": "playclock-update",
  "match_id": 123,
  "playclock": {
    "id": 234,
    "playclock": 40,
    "playclock_status": "running"
  }
}

// match-update
{
  "type": "match-update",
  "match_id": 123,
  "data": {
    "match": {...},
    "teams_data": {...},
    "scoreboard_data": {...},
    "match_data": {...}
  }
}
```

### Architecture Decisions

**Why Combined Initial Load:**

1. **Performance**: Single `asyncio.gather` fetches all data concurrently instead of 5 sequential requests
2. **Atomicity**: All initial data arrives together, no partial state issues
3. **Frontend Integration**: Frontend can use WebSocket as primary data source, avoiding race conditions
4. **Backward Compatibility**: Existing update messages unchanged, gradual migration possible

**Why Full Data on Updates (vs. Deltas):**

1. **Simplicity**: No complex change tracking or delta calculation logic
2. **Consistency**: Always have full data for each update type
3. **Network Overhead**: Acceptable for typical use case (< 1MB per message)
4. **Future-Proof**: Full data makes conflicts easier to resolve (last-write-wins)

**Why HTTP as Fallback (vs. WebSocket-only):**

1. **Robustness**: Works even if WebSocket fails to connect
2. **SSR Support**: Initial HTML render can use HTTP data before WebSocket connects
3. **Debugging**: Can test HTTP separately from WebSocket
4. **Graceful Degradation**: Falls back gracefully if WebSocket unavailable

### Implementation Status

- ✅ STAB-148: Main WebSocket refactor issue
- ✅ STAB-149: Backend parallel data fetching implementation
- ✅ STAB-150: Comprehensive backend testing
- ✅ STAF-204: Frontend WebSocket service handler
- ✅ STAF-202: Frontend scoreboard-view component
- ✅ STAF-203: Frontend scoreboard-admin component

**See**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md#websocket-endpoints) for complete WebSocket message specifications

### File Management (`src/helpers/`)

**Services**:
- `FileService`: File operations (read, write, delete, move)
- `ImageProcessingService`: Image resizing and optimization
- `UploadService`: File upload handling with validation
- `DownloadService`: File download handling

**Features**:
- Secure file uploads
- Image optimization
- Static file serving
- Logo management for teams and tournaments

## Data Flow Examples

### Creating a Team

```
1. Client: POST /api/teams/ with team data
2. API Layer: TeamAPIRouter.create_team_endpoint()
   - Validates request with TeamSchemaCreate
3. Service Layer: TeamServiceDB.create()
   - Validates business logic
   - Creates TeamDB model
4. Data Access Layer: BaseServiceDB.create()
   - Adds to session
   - Commits transaction
5. Database: PostgreSQL
   - Inserts new record
   - Returns inserted row
6. Response: TeamSchema with id and created_at
```

### Fetching Match with Full Data

```
1. Client: GET /api/matches/id/{match_id}/players_fulldata/
2. API Layer: MatchAPIRouter.get_match_full_data_endpoint()
3. Service Layer: MatchServiceDB.get_player_by_match_full_data()
   - Uses selectinload for nested relationships
   - Fetches player_team_tournament → player → person → position
   - Transforms data into dictionary structure
4. Data Access Layer: BaseServiceDB.get_with_relationships()
5. Database: PostgreSQL with JOINs
6. Response: Complete match data dictionary
```

### Real-time Game Clock Updates

```
1. Clock Orchestrator: ClockOrchestrator._run_loop()
     - Single centralized loop checking all running clocks every 100ms
     - Uses ClockStateMachine for in-memory state tracking
     - Calculates current value from elapsed time (no DB read)
     - Registers/unregisters playclocks and gameclocks dynamically
2. Service Callbacks: Trigger NOTIFY and update database
     - PlayClockServiceDB.trigger_update_playclock()
     - GameClockServiceDB.trigger_update_gameclock()
     - Stop callbacks when clocks reach 0
3. WebSocket Manager: Broadcasts to all connected clients
     - Broadcasts every second with calculated value (no DB round-trip)
4. Clients: Receive real-time clock updates via WebSocket
```

**Note:** For comprehensive documentation on clock handling system, see [CLOCK_HANDLING.md](CLOCK_HANDLING.md) which covers:
- Complete clock architecture diagrams
- State machine transitions and timing calculations
- Database triggers and notification flow
- WebSocket message processing
- Start/stop/pause/reset operations
- Differences between PlayClock and GameClock
- Troubleshooting common issues

**Architecture Benefits:**
- Single loop replaces per-clock background tasks
- Reduced resource usage (one async task instead of one per clock)
- Centralized callback pattern for extensibility
- Immediate database updates on state changes (no sync interval needed)

## Cross-Domain Communication

### Service-to-Service Communication

**Pattern**: Services communicate through the service registry, never direct imports

**Example Chain**:
```
MatchService → (registry) → TournamentService → (registry) → SportService
```

**Benefits**:
- No circular imports
- Easy to mock in tests
- Loose coupling
- Centralized dependency management

### Data Synchronization

**EESL Integration**: External data synchronization
- Parse tournaments, teams, players from EESL system
- Sync match data in real-time
- Update statistics and standings

**WebSocket Events**: Real-time updates
- Game clock changes
- Score updates
- Football events (goals, cards, substitutions)

## Error Handling Architecture

### Exception Hierarchy (`src/core/exceptions.py`)

```
AppException (base)
├── ValidationError (400)
├── NotFoundError (404)
├── DatabaseError (500)
├── BusinessLogicError (422)
├── ExternalServiceError (503)
├── ConfigurationError (500)
├── AuthenticationError (401)
├── AuthorizationError (403)
├── ConcurrencyError (409)
├── FileOperationError (500)
└── ParsingError (400)
```

### Global Exception Handlers (`src/core/exception_handler.py`)

All custom exceptions are caught and converted to appropriate HTTP responses with proper status codes.

### Logging Architecture

**Levels**:
- `debug`: Detailed operation tracking
- `info`: Significant operations (creates, updates)
- `warning`: Expected but noteworthy situations (validation errors)
- `error`: Unexpected errors (database failures)
- `critical`: Unexpected errors that should rarely trigger

**Format**: Structured JSON logging with consistent format across all services

## Configuration Management

### Pydantic Settings (`src/core/config.py`)

- Database settings
- Application settings
- CORS configuration
- Path settings
- SSL configuration

### Configuration Validation

**Validation Levels**:
1. **Database Settings**: Required fields, port ranges, connection string validation
2. **Application Settings**: CORS origin format, SSL file pairs
3. **Path Validation**: Required paths must exist and be readable
4. **Database Connection**: Tests connectivity on startup

**See**: `CONFIGURATION_VALIDATION.md` for complete documentation

## Testing Architecture

### Test Organization

```
tests/
├── conftest.py           # Shared fixtures
├── fixtures.py           # Custom fixtures
├── factories.py          # Test data factories
├── test_db_services/     # Service layer tests
├── test_views/          # API endpoint tests
└── test_mixins/         # Mixin tests
```

### Test Database

- PostgreSQL only (not SQLite) for production compatibility
- Transaction rollback per test (fast cleanup)
- No Alembic migrations (direct table creation)
- Docker container for test database isolation

### Test Patterns

- Use `@pytest.mark.asyncio` for async tests
- Use factory classes for test data
- Test both success and error paths
- Use descriptive docstrings

## Performance Optimizations

### Database Level

- Connection pooling with asyncpg
- Selective relationship loading (selectinload, lazyload)
- Efficient query patterns with SQLAlchemy 2.0
- Index optimization on frequently queried fields

### Application Level

- Async/await for all I/O operations
- Background tasks for clock management
- WebSocket connection pooling
- Efficient data serialization

### Testing Level

- Transaction rollback for fast cleanup
- No database echo in test fixtures
- Session-scoped database engine where possible
- Parallel test execution support (pytest-xdist)

## Deployment Architecture

### Development

- Hot reload with uvicorn
- Local PostgreSQL database
- Console logging
- Debug mode enabled

### Production

- Gunicorn with Uvicorn workers
- Nginx reverse proxy
- SSL/TLS termination
- Structured JSON logging
- Docker containerization
- Health checks and monitoring

### Docker Compose Services

- `app`: Main FastAPI application
- `nginx`: Reverse proxy and static file serving
- `certbot`: SSL certificate management
- `db`: PostgreSQL database
- `redis`: Caching and pub/sub (optional)

## Security Considerations

### Input Validation

- Pydantic schemas for all request validation
- SQL injection prevention via SQLAlchemy ORM
- XSS protection via FastAPI middleware

### Authentication/Authorization

- Ready for integration with auth providers
- Exception hierarchy includes auth errors
- CORS configuration

### File Upload Security

- File type validation
- Size limits
- Secure file paths
- Image processing to prevent malicious uploads

## Future Enhancements

### Event-Driven Architecture

Consider implementing event-driven architecture for truly decoupled cross-domain operations:

- Event bus for domain events
- Event handlers for side effects
- Event replay support
- Event versioning

**Example**:
```python
# MatchService emits event
await event_bus.emit("match.created", match_id=match.id)

# TeamService subscribes to events
@event_bus.subscribe("match.created")
async def on_match_created(match_id):
    # Update team statistics
    pass
```

### Caching Layer

Add Redis caching for frequently accessed data:
- Tournament listings
- Team rosters
- Player statistics
- Scoreboard data

### API Rate Limiting

Implement rate limiting for API endpoints:
- Per-client rate limits
- Global rate limits
- Exponential backoff

### API Versioning

Implement API versioning strategy:
- URL-based versioning (/v1/, /v2/)
- Header-based versioning
- Backward compatibility

## Summary

The StatsBoards Backend architecture emphasizes:

1. **Clear separation of concerns** through layered architecture
2. **Loose coupling** via service registry pattern
3. **Type safety** with comprehensive type hints
4. **Performance** through async/await and connection pooling
5. **Testability** with dependency injection and factory patterns
6. **Maintainability** with consistent patterns and conventions
7. **Scalability** through modular design and async operations

This architecture supports the application's requirements for real-time sports statistics management while maintaining clean, maintainable, and testable code.
