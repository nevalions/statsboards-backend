# Overview

This document explains the real-time WebSocket data flow between PostgreSQL triggers, WebSocket listeners, and connected clients.

## High-Level Flow

```
PostgreSQL triggers (pg_notify)
  │
  ▼
MatchDataWebSocketManager (asyncpg listeners)
  │
  ▼
ConnectionManager (queues + subscriptions)
  │
  ▼
MatchWebSocketHandler (per-connection processing)
  │
  ▼
Clients
```

## Initial Load

On connection, the handler fetches all match data and sends a single `initial-load` message.

See `docs/websockets/message-types.md` for payload details.
