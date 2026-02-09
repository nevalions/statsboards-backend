# Overview

The clock handling system manages real-time playclocks and gameclocks for matches. It uses in-memory state machines for timing, PostgreSQL triggers for notifications, and WebSockets for client delivery.

## Key Characteristics

- Dual clock types: PlayClock and GameClock
- State machine based timing (no per-second DB writes)
- Single orchestrator loop coordinates updates
- PostgreSQL NOTIFY triggers fire on state changes
- WebSocket delivery to subscribed clients
- Client-side clock calculation using `started_at_ms`

## Architecture (High Level)

```
Client
  │ HTTP/WebSocket
  ▼
Views/Services
  │ DB updates (start/stop/pause/reset)
  ▼
PostgreSQL triggers (pg_notify)
  │
  ▼
WebSocket manager → Connection manager queues → Match handler
  │
  ▼
Clients receive updates
```

## State Machine

Both clocks use the same state machine pattern:

```python
class ClockStateMachine:
    def __init__(
        self,
        clock_id: int,
        initial_value: int,
        direction: ClockDirection = ClockDirection.DOWN,
        max_value: int = 720,
    ) -> None:
        self.clock_id = clock_id
        self.value = initial_value
        self.direction = direction
        self.max_value = max_value
        self.status = ClockStatus.STOPPED
        self.started_at_ms: int | None = None

    def get_current_value(self) -> int:
        if self.status != ClockStatus.RUNNING or self.started_at_ms is None:
            return self.value
        elapsed_ms = int(time.time() * 1000) - self.started_at_ms
        elapsed_sec = elapsed_ms // 1000

        if self.direction == ClockDirection.DOWN:
            return max(0, self.value - elapsed_sec)
        else:
            return min(self.max_value, self.value + elapsed_sec)
```

State transitions:

```
stopped ── start ──▶ running ── stop ──▶ stopped
                     │
                     └─ pause ─▶ paused ── start ─▶ running
```
