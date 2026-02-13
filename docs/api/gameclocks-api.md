# Gameclocks API

Manage game clocks for matches. The game clock counts total game time for quarters and halves in American football. It supports both countdown (down) and count-up (up) directions.

When `use_sport_preset=true`, gameclock max can be period-aware based on the sport preset's `period_clock_variant`:
- `per_period` (default): effective max remains base `gameclock_max`
- `cumulative`: effective max is `base gameclock_max * current_period_index`

Soccer example (`base gameclock_max=2700`, two halves):
- `period.1` => effective max `2700` (45:00)
- `period.2` => effective max `5400` (90:00)

### Response Schemas

```typescript
interface GameClockSchema {
  id: number;
  gameclock: number; // Total time in seconds (max 10000), default 720 (12 minutes)
  gameclock_max: number | null; // Maximum time in seconds, default 720
  direction: string; // Clock direction: "down" or "up" (default: "down")
  on_stop_behavior: string; // Behavior when stopped: "hold" or "reset" (default: "hold")
  gameclock_status: string; // Status: "stopped", "running", "paused" (max 50 chars)
  gameclock_time_remaining: number | null; // Remaining time during countdown
  match_id: number | null; // Associated match ID
  version: number; // Version number, starts at 1, increments on each update
  started_at_ms: number | null; // Unix timestamp (ms) when clock started, null if paused/stopped
  server_time_ms: number | null; // Server time (ms) when response generated
  use_sport_preset: boolean; // Whether to use sport preset values (default: true)
}

interface GameClockSchemaCreate {
  gameclock: number; // Total time in seconds (max 10000), default 720
  gameclock_max: number | null; // Optional max time
  direction: string; // Clock direction: "down" or "up" (default: "down")
  on_stop_behavior: string; // Behavior when stopped: "hold" or "reset" (default: "hold")
  gameclock_status: string; // Status, defaults to "stopped" (max 50 chars)
  gameclock_time_remaining: number | null; // Optional remaining time
  match_id: number | null; // Optional match ID
  version?: number; // Version number, defaults to 1
  started_at_ms?: number | null; // Optional start timestamp (ms)
  use_sport_preset?: boolean; // Use sport preset values (default: true)
}

interface GameClockSchemaUpdate {
  gameclock: number | null; // Optional time in seconds
  gameclock_max: number | null; // Optional max time
  direction: string | null; // Clock direction: "down" or "up"
  on_stop_behavior: string | null; // Behavior when stopped: "hold" or "reset"
  gameclock_status: string | null; // Optional status
  gameclock_time_remaining: number | null; // Optional remaining time
  match_id: number | null; // Optional match ID
  started_at_ms?: number | null; // Optional start timestamp (ms)
  use_sport_preset?: boolean; // Use sport preset values
}
```

---

### POST /api/gameclock/

Create a new game clock.

**Endpoint:**
```
POST /api/gameclock/
```

**Request Body:**
```json
{
  "gameclock": 720,
  "gameclock_max": 720,
  "direction": "down",
  "on_stop_behavior": "hold",
  "gameclock_status": "stopped",
  "match_id": 123,
  "use_sport_preset": true
}
```

**Request Schema:**
```typescript
interface GameClockSchemaCreate {
  gameclock: number; // Total time in seconds (max 10000), default 720
  gameclock_max: number | null; // Optional maximum time
  gameclock_status: string; // Status, defaults to "stopped" (max 50 chars)
  gameclock_time_remaining: number | null; // Optional remaining time
  match_id: number | null; // Optional associated match ID
  version?: number; // Version number, defaults to 1
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "gameclock": 720,
  "gameclock_max": 720,
  "direction": "down",
  "on_stop_behavior": "hold",
  "gameclock_status": "stopped",
  "gameclock_time_remaining": null,
  "match_id": 123,
  "version": 1,
  "use_sport_preset": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Bad request - validation error |
| 500 | Internal server error |

---

### PUT /api/gameclock/{item_id}/

Update a game clock by ID.

**Endpoint:**
```
PUT /api/gameclock/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | GameClock ID to update |

**Request Body:**
```json
{
  "gameclock_status": "running",
  "direction": "down"
}
```

**Request Schema:**
```typescript
interface GameClockSchemaUpdate {
  gameclock: number | null; // Optional time in seconds
  gameclock_max: number | null; // Optional max time
  gameclock_status: string | null; // Optional status
  gameclock_time_remaining: number | null; // Optional remaining time
  match_id: number | null; // Optional match ID
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "gameclock": 720,
  "gameclock_max": 720,
  "direction": "down",
  "on_stop_behavior": "hold",
  "gameclock_status": "running",
  "gameclock_time_remaining": 720,
  "match_id": 123,
  "version": 2,
  "use_sport_preset": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Gameclock not found |
| 409 | Error updating gameclock |
| 500 | Internal server error |

---

### PUT /api/gameclock/id/{item_id}/

Update a game clock by ID with JSONResponse format.

**Endpoint:**
```
PUT /api/gameclock/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | GameClock ID to update |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "gameclock": 720,
    "gameclock_status": "running",
    "gameclock_time_remaining": 720,
    "match_id": 123,
    "version": 2
  },
  "status_code": 200,
  "success": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Gameclock not found |
| 500 | Internal server error |

---

### PUT /api/gameclock/id/{gameclock_id}/running/

Start the game clock and begin countdown.

**Endpoint:**
```
PUT /api/gameclock/id/{gameclock_id}/running/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `gameclock_id` | integer | Yes | GameClock ID |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "gameclock": 720,
    "gameclock_max": 720,
    "direction": "down",
    "on_stop_behavior": "hold",
    "gameclock_status": "running",
    "gameclock_time_remaining": 720,
    "match_id": 123,
    "version": 1,
    "started_at_ms": 1737648000000,
    "server_time_ms": 1737648000050,
    "use_sport_preset": true
  },
  "status_code": 200,
  "success": true,
  "message": "Game clock ID:1 running"
}
```

**Behavior:**
- If gameclock was not running, updates status to "running" and sets `gameclock_time_remaining` to current `gameclock` value
- Sets `started_at_ms` to current server time in milliseconds (Unix timestamp)
- Updates state machine with `started_at_ms` for accurate time calculation
- Registers gameclock with ClockOrchestrator for centralized management
- ClockOrchestrator decrements `gameclock_time_remaining` every second based on elapsed time from `started_at_ms`
- Includes `server_time_ms` in response for frontend time synchronization
- Invalidates gameclock cache to trigger immediate WebSocket updates to all connected clients
- If gameclock was already running, returns current state with message

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

**Error Response (500):**
```json
{
  "content": null,
  "status_code": 500,
  "success": false,
  "message": "Error starting gameclock: <error details>"
}
```

---

### PUT /api/gameclock/id/{item_id}/paused/

Pause the game clock.

**Endpoint:**
```
PUT /api/gameclock/id/{item_id}/paused/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | GameClock ID |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "gameclock": 650,
    "gameclock_max": 720,
    "direction": "down",
    "on_stop_behavior": "hold",
    "gameclock_status": "paused",
    "gameclock_time_remaining": 650,
    "match_id": 123,
    "version": 2,
    "started_at_ms": null,
    "server_time_ms": 1737648070000,
    "use_sport_preset": true
  },
  "status_code": 200,
  "success": true,
  "message": "Game clock ID:1 paused"
}
```

**Behavior:**
- Pauses the countdown timer by pausing the state machine
- Calculates current value from state machine using `started_at_ms` elapsed time
- Updates `gameclock` field with the current remaining time from the state machine
- Updates `gameclock_time_remaining` with the current value
 - Sets `started_at_ms` to `null` (cleared when clock is paused)
 - Sets `gameclock_status` to "paused"
 - Includes `server_time_ms` in response for frontend time synchronization
 - Invalidates gameclock cache to trigger immediate WebSocket updates to all connected clients

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Game clock not found |
| 500 | Internal server error |

**Error Response (404):**
```json
{
  "content": null,
  "status_code": 404,
  "success": false,
  "message": "Game clock ID:{id} not found"
}
```

**Error Response (500):**
```json
{
  "content": null,
  "status_code": 500,
  "success": false,
  "message": "Error pausing gameclock: <error details>"
}
```

---

### PUT /api/gameclock/id/{item_id}/{item_status}/{sec}/

Reset the game clock to a specific time and status.

**Endpoint:**
```
PUT /api/gameclock/id/{item_id}/{item_status}/{sec}/
```

**Path Parameters:**

| Parameter | Type | Required | Description | Examples |
|-----------|------|----------|-------------|------------|
| `item_id` | integer | Yes | GameClock ID | - |
| `item_status` | string | Yes | New status | "stopped", "running", "paused" |
| `sec` | integer | Yes | Time in seconds | 720, 900, 1800 |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "gameclock": 900,
    "gameclock_max": 720,
    "direction": "down",
    "on_stop_behavior": "hold",
    "gameclock_status": "stopped",
    "gameclock_time_remaining": null,
    "match_id": 123,
    "use_sport_preset": true
  },
  "status_code": 200,
  "success": true
}
```

**Behavior:**
- Updates gameclock to specified time and status
- Commonly used to reset quarter/half times (900s = 15 min, 1800s = 30 min)
- For preset-managed matches (`use_sport_preset=true`), period transitions may recalculate `gameclock_max` automatically from preset variant and current period.
- Invalidates gameclock cache to trigger immediate WebSocket updates to all connected clients

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Game clock not found |
| 500 | Internal server error |

**Error Response (404):**
```json
{
  "content": null,
  "status_code": 404,
  "success": false,
  "message": "Game clock ID:{id} not found"
}
```

**Error Response (500):**
```json
{
  "content": null,
  "status_code": 500,
  "success": false,
  "message": "Error resetting gameclock: <error details>"
}
```

---

### DELETE /api/gameclock/id/{model_id}

Delete a game clock by ID. Requires admin role.

**Endpoint:**
```
DELETE /api/gameclock/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | GameClock ID to delete |

**Response (200 OK):**
```json
{
  "detail": "Gameclock 1 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | Gameclock not found |
| 500 | Internal server error |

---
