# Overview

StatsBoards Backend is a FastAPI service for sports tournaments, matches, and real-time game data. The architecture is layered, domain-driven, and built around async I/O.

Supported sports:

- American football
- Flag football
- Extensible for additional sports

## High-Level Architecture

```
Client (web/mobile/integrations)
  │ HTTP/WebSocket
  ▼
API Layer (FastAPI routers, validation, exception handling, WebSocket)
  ▼
Service Layer (business logic, orchestration, service registry)
  ▼
Data Access Layer (BaseServiceDB, SQLAlchemy async ORM)
  ▼
PostgreSQL (migrations, triggers, pooling)
```

## Core Architectural Patterns

### Layered Architecture

- API layer: request/response and routing
- Service layer: business logic
- Data access layer: DB reads/writes
- Cross-cutting: logging, configuration, error handling, WebSocket

### Domain-Driven Design

Each domain module contains:

- Models
- Schemas
- Services
- Views (routers)

Example structure:

```
src/teams/
  db_services.py
  schemas.py
  views.py
```

### Service Registry Pattern

- Central registration: `src/core/service_initialization.py`
- Access: `service_registry.get("service_name")`
- Avoids circular imports and enables DI

See `docs/SERVICE_LAYER_DECOUPLING.md` for details.

### Router Registry Pattern

- Central config: `src/core/router_registry.py`
- Priority-ordered registration
- Enables toggling routers without touching `main.py`

See `docs/ROUTER_REGISTRY.md` for details.

### Base Router and Service Patterns

- `BaseRouter` adds standard CRUD endpoints
- `BaseServiceDB` provides core CRUD operations
- Mixins add query and relationship helpers

### Async Everywhere

- Async SQLAlchemy + asyncpg
- Async WebSockets
- Async context managers for sessions
