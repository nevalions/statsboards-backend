# Components

## Database Models (`src/core/models/`)

- SQLAlchemy 2.0 async models
- `Mapped` + `mapped_column`
- Relationship definitions with `back_populates`
- Mixins for shared fields

## Service Layer (`src/*/db_services.py`)

- Inherits `BaseServiceDB`
- Uses service registry for cross-service dependencies
- Structured logging
- Decorator-based exception handling

## API Layer (`src/*/views.py`)

- `BaseRouter` for standard endpoints
- Custom endpoints appended after base routes
- Role-based access via `require_roles`

## WebSocket Management (`src/websocket/`, `src/utils/websocket/`)

- DB triggers → asyncpg listeners → connection manager queues → handlers
- Message types include `match-update`, `gameclock-update`, `playclock-update`, `event-update`, `statistics-update`, `players-update`
- `ping`/`pong` used for health and stale connection cleanup

## File Management (`src/helpers/`)

- Upload/download helpers
- Safe file operations
- Consistent path handling and validation

## Architecture Decisions

- Prefer service registry over direct service instantiation
- Prefer router registry for centralized configuration
- Use async DB I/O throughout

## Implementation Status

- Core API, auth, and sports domains implemented
- WebSocket flows and clock orchestration in place
- Ongoing improvements in tests and error handling
