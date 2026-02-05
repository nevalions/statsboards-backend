# Troubleshooting

## Clock Not Updating

Check:

- Orchestrator running and clock registered
- State machine status is RUNNING
- `started_at_ms` is set

## Notifications Not Received

Check:

- Trigger conditions (status/value change only)
- Listener subscriptions in `MatchDataWebSocketManager`
- Cache invalidation happening before send

## Negative Values

State machine uses `max(0, ...)` to prevent negatives. If negatives appear, verify client-side calculation.

## Debugging Helpers

Enable debug logging on:

- Orchestrator
- WebSocket manager
- Clock services

Inspect active clocks:

```python
from src.clocks.clock_orchestrator import clock_orchestrator
print(clock_orchestrator.running_playclocks.keys())
print(clock_orchestrator.running_gameclocks.keys())
```
