# Data Flow

## Creating a Team

1. Client submits POST to `/api/teams/`
2. Router validates schema
3. Service applies business rules
4. DB insert via BaseServiceDB
5. Response serialized to schema

## Fetching Match with Full Data

1. Client calls `/api/matches/id/{id}/with-details/`
2. Service loads match and related entities (teams, tournament, sponsors)
3. Response uses combined schema

## Real-Time Game Clock Updates

1. State change updates DB
2. Trigger emits `gameclock_change`
3. WebSocket listener enqueues `gameclock-update`
4. Clients update UI using `started_at_ms`

## Cross-Domain Communication

- Services call other services via service registry
- Avoid direct imports to prevent circular dependencies
- Use shared helpers for common relationship lookups
