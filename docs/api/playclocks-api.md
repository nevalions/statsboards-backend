# Playclocks API

Manage play clocks for matches. The play clock counts down the time between plays in American football.

### Response Schemas

```typescript
interface PlayClockSchema {
  id: number;
  playclock: number | null; // Current time in seconds (max 10000)
  playclock_status: string; // Status: "stopped", "running", "paused" (max 50 chars)
  match_id: number | null; // Associated match ID
  version: number; // Version number, starts at 1, increments on each update
  started_at_ms: number | null; // Unix timestamp (ms) when clock started, null if paused/stopped
  server_time_ms: number | null; // Server time (ms) when response generated
}

interface PlayClockSchemaCreate {
  playclock: number | null; // Optional time in seconds (max 10000)
  playclock_status: string; // Status, defaults to "stopped" (max 50 chars)
  match_id: number | null; // Optional match ID
  version?: number; // Version number, defaults to 1
  started_at_ms?: number | null; // Optional start timestamp (ms)
}

interface PlayClockSchemaUpdate {
  playclock: number | null; // Optional time in seconds
  playclock_status: string | null; // Optional status
  match_id: number | null; // Optional match ID
  started_at_ms?: number | null; // Optional start timestamp (ms)
}
```

---

### POST /api/playclock/

Create a new play clock.

**Endpoint:**
```
POST /api/playclock/
```

**Request Body:**
```json
{
  "playclock": 40,
  "playclock_status": "stopped",
  "match_id": 123
}
```

**Request Schema:**
```typescript
interface PlayClockSchemaCreate {
  playclock: number | null; // Optional time in seconds (max 10000)
  playclock_status: string; // Status, defaults to "stopped" (max 50 chars)
  match_id: number | null; // Optional associated match ID
  version?: number; // Version number, defaults to 1
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "playclock": 40,
  "playclock_status": "stopped",
  "match_id": 123,
  "version": 1,
  "started_at_ms": null,
  "server_time_ms": 1737648070000
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Bad request - validation error |
| 500 | Internal server error - database error |

---

### PUT /api/playclock/{item_id}/

Update a play clock by ID.

**Endpoint:**
```
PUT /api/playclock/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | PlayClock ID to update |

**Request Body:**
```json
{
  "playclock": 35,
  "playclock_status": "running"
}
```

**Request Schema:**
```typescript
interface PlayClockSchemaUpdate {
  playclock: number | null; // Optional time in seconds
  playclock_status: string | null; // Optional status
  match_id: number | null; // Optional match ID
  version?: number; // Optional version number (auto-incremented on update)
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "playclock": 35,
  "playclock_status": "running",
  "match_id": 123,
  "version": 2,
  "started_at_ms": 1737648000000,
  "server_time_ms": 1737648000050
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Playclock not found |
| 500 | Internal server error |

---

### PUT /api/playclock/id/{item_id}/

Update a play clock by ID with JSONResponse format.

**Endpoint:**
```
PUT /api/playclock/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | PlayClock ID to update |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "playclock": 35,
    "playclock_status": "running",
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
| 404 | Playclock not found |
| 500 | Internal server error |

---

### GET /api/playclock/id/{item_id}/

Get a play clock by ID.

**Endpoint:**
```
GET /api/playclock/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | PlayClock ID to retrieve |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "title": "Playclock",
    "description": "Match playclock"
  },
  "status_code": 200,
  "success": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Playclock not found |
| 500 | Internal server error |

---

### PUT /api/playclock/id/{item_id}/running/{sec}/

Start the play clock and begin countdown.

**Endpoint:**
```
PUT /api/playclock/id/{item_id}/running/{sec}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | PlayClock ID |
| `sec` | integer | Yes | Starting time in seconds |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "playclock": 40,
    "playclock_status": "running",
    "match_id": 123,
    "version": 2,
    "started_at_ms": 1737648000000,
    "server_time_ms": 1737648000050
  },
  "status_code": 200,
  "success": true
}
```

**Behavior:**
- Enables match data clock queues for SSE
- If playclock was not already running, updates to specified time and status "running"
- Sets `started_at_ms` to current server time in milliseconds (Unix timestamp)
- Updates state machine with `started_at_ms` for accurate time calculation
- Registers playclock with ClockOrchestrator for centralized management
- ClockOrchestrator decrements playclock every second until stopped based on elapsed time from `started_at_ms`
- Includes `server_time_ms` in response for frontend time synchronization

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Playclock not found |
| 500 | Internal server error - database error |

---

### PUT /api/playclock/id/{item_id}/{item_status}/{sec}/

Reset the play clock to a specific time and status.

**Endpoint:**
```
PUT /api/playclock/id/{item_id}/{item_status}/{sec}/
```

**Path Parameters:**

| Parameter | Type | Required | Description | Examples |
|-----------|------|----------|-------------|------------|
| `item_id` | integer | Yes | PlayClock ID | - |
| `item_status` | string | Yes | New status | "stopped", "running", "paused" |
| `sec` | integer | Yes | Time in seconds | 25, 40, 25 |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "playclock": 25,
    "playclock_status": "stopped",
    "match_id": 123,
    "started_at_ms": null,
    "server_time_ms": 1737648070000
  },
  "status_code": 200,
  "success": true
}
```

**Behavior:**
- Updates playclock to specified time and status
- Commonly used to reset to 40 seconds (stopped) for new play

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Playclock not found |
| 500 | Internal server error - database error |

---

### PUT /api/playclock/id/{item_id}/stopped/

Stop the play clock and clear time.

**Endpoint:**
```
PUT /api/playclock/id/{item_id}/stopped/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | PlayClock ID |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "playclock": null,
    "playclock_status": "stopped",
    "match_id": 123,
    "started_at_ms": null,
    "server_time_ms": 1737648070000
  },
  "status_code": 200,
  "success": true
}
```

**Behavior:**
- Sets playclock to `null` and status to "stopped"
- Calculates current value from state machine using `started_at_ms` elapsed time
- Sets `started_at_ms` to `null` (cleared when clock is paused)
- Includes `server_time_ms` in response for frontend time synchronization
- Used to clear clock display between plays

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Playclock not found |
| 500 | Internal server error - database error |

---

### DELETE /api/playclock/id/{model_id}

Delete a play clock by ID. Requires admin role.

**Endpoint:**
```
DELETE /api/playclock/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | PlayClock ID to delete |

**Response (200 OK):**
```json
{
  "detail": "Playclock 1 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | Playclock not found |
| 500 | Internal server error |

---
