# Clock Operations

## PlayClock

### Start

`PUT /api/playclock/id/{item_id}/running/{sec}/`

Flow:

1. Enable queues and state machine
2. Update DB with `playclock`, `playclock_status`, `started_at_ms`
3. Trigger fires, WebSocket notifies

### Stop/Reset

`PUT /api/playclock/id/{item_id}/{item_status}/{sec}/`

`item_status` should be one of: `stopped`, `running`, `paused`, `stopping`.

### Stop (clear to None)

`PUT /api/playclock/id/{item_id}/stopped/`

## GameClock

### Start

`PUT /api/gameclock/id/{gameclock_id}/running/`

Uses DB value for `gameclock` rather than a URL parameter.

### Pause

`PUT /api/gameclock/id/{item_id}/paused/`

### Reset

`PUT /api/gameclock/id/{item_id}/{item_status}/{sec}/`

`item_status` must map to a `ClockStatus` value (`stopped`, `running`, `paused`, `stopping`).

### Period-Aware Reset

`PUT /api/gameclock/id/{gameclock_id}/reset/`

Computes reset value server-side based on sport preset and current period:

- `direction=down` → resets to `gameclock_max`
- `direction=up` + `per_period` → resets to `0`
- `direction=up` + `cumulative` → resets to `base_max * (period_index - 1)`

Example (soccer, base_max=2700):
- Period 1 reset → `0`
- Period 2 reset → `2700`

## Client-Side Calculation

Clients calculate current values using `started_at_ms`:

```javascript
function calculateCurrent(startTimeMs, initialValue) {
  const elapsedSec = Math.floor((Date.now() - startTimeMs) / 1000);
  return Math.max(0, initialValue - elapsedSec);
}
```
