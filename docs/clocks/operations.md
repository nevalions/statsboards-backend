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

## Client-Side Calculation

Clients calculate current values using `started_at_ms`:

```javascript
function calculateCurrent(startTimeMs, initialValue) {
  const elapsedSec = Math.floor((Date.now() - startTimeMs) / 1000);
  return Math.max(0, initialValue - elapsedSec);
}
```
