# Connection and Queues

## Connection Manager

Location: `src/utils/websocket/websocket_manager.py`

Each client gets:

- A WebSocket connection
- A per-client `asyncio.Queue`
- A match subscription entry

```python
self.active_connections: dict[str, WebSocket] = {}
self.queues: dict[str, asyncio.Queue] = {}
self.match_subscriptions: dict[str | int, list[str]] = {}
self.last_activity: dict[str, float] = {}
```

## Queue Flow

1. Client connects with `client_id` and `match_id`
2. Queue created: `queues[client_id] = asyncio.Queue()`
3. Subscription added: `match_subscriptions[match_id].append(client_id)`
4. Messages for a match are enqueued to all subscribed client queues
5. `process_data_websocket()` reads from the queue and sends over the socket

## Ping/Pong

The match WebSocket handler sends a `ping` every 60s. Clients respond with `pong` to update activity timestamps.
