# Sport Scoreboard Presets API

Manage sport-specific scoreboard and gameclock presets. Presets define default configurations for different sports, including gameclock settings (direction, behavior) and scoreboard display options.

### Response Schemas

```typescript
interface SportScoreboardPresetSchema {
  id: number;
  title: string; // Max 255 characters
  gameclock_max: number | null; // Maximum gameclock time in seconds, default 720
  direction: string; // Clock direction: "down" or "up" (default: "down")
  on_stop_behavior: string; // Behavior when stopped: "hold" or "reset" (default: "hold")
  is_qtr: boolean; // Show quarter indicator (default: true)
  is_time: boolean; // Show time display (default: true)
  is_playclock: boolean; // Show playclock (default: true)
  is_downdistance: boolean; // Show down and distance (default: true)
}

interface SportScoreboardPresetSchemaCreate {
  title: string; // Max 255 characters
  gameclock_max: number | null; // Optional max time in seconds, default 720
  direction: string; // Clock direction: "down" or "up" (default: "down")
  on_stop_behavior: string; // Behavior when stopped: "hold" or "reset" (default: "hold")
  is_qtr: boolean; // Show quarter indicator, defaults to true
  is_time: boolean; // Show time display, defaults to true
  is_playclock: boolean; // Show playclock, defaults to true
  is_downdistance: boolean; // Show down and distance, defaults to true
}

interface SportScoreboardPresetSchemaUpdate {
  title: string | null; // Optional - Max 255 characters
  gameclock_max: number | null; // Optional max time in seconds
  direction: string | null; // Optional clock direction: "down" or "up"
  on_stop_behavior: string | null; // Optional behavior when stopped: "hold" or "reset"
  is_qtr: boolean | null; // Optional quarter indicator
  is_time: boolean | null; // Optional time display
  is_playclock: boolean | null; // Optional playclock
  is_downdistance: boolean | null; // Optional down and distance
}
```

---

### POST /api/sport-scoreboard-presets/

Create a new sport scoreboard preset.

**Endpoint:**
```
POST /api/sport-scoreboard-presets/
```

**Request Body:**
```json
{
  "title": "American Football Preset",
  "gameclock_max": 720,
  "direction": "down",
  "on_stop_behavior": "hold",
  "is_qtr": true,
  "is_time": true,
  "is_playclock": true,
  "is_downdistance": true
}
```

**Request Schema:**
```typescript
interface SportScoreboardPresetSchemaCreate {
  title: string; // Max 255 characters
  gameclock_max: number | null; // Optional max time in seconds
  direction: string; // Clock direction: "down" or "up"
  on_stop_behavior: string; // Behavior when stopped: "hold" or "reset"
  is_qtr: boolean; // Show quarter indicator
  is_time: boolean; // Show time display
  is_playclock: boolean; // Show playclock
  is_downdistance: boolean; // Show down and distance
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "American Football Preset",
  "gameclock_max": 720,
  "direction": "down",
  "on_stop_behavior": "hold",
  "is_qtr": true,
  "is_time": true,
  "is_playclock": true,
  "is_downdistance": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Bad request - validation error |
| 500 | Internal server error |

---

### PUT /api/sport-scoreboard-presets/{item_id}/

Update a sport scoreboard preset by ID.

**Endpoint:**
```
PUT /api/sport-scoreboard-presets/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Preset ID to update |

**Request Body:**
```json
{
  "title": "American Football Preset - Updated",
  "direction": "up",
  "on_stop_behavior": "reset"
}
```

**Request Schema:**
```typescript
interface SportScoreboardPresetSchemaUpdate {
  title: string | null; // Optional - Max 255 characters
  gameclock_max: number | null; // Optional max time in seconds
  direction: string | null; // Optional clock direction: "down" or "up"
  on_stop_behavior: string | null; // Optional behavior when stopped: "hold" or "reset"
  is_qtr: boolean | null; // Optional quarter indicator
  is_time: boolean | null; // Optional time display
  is_playclock: boolean | null; // Optional playclock
  is_downdistance: boolean | null; // Optional down and distance
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "American Football Preset - Updated",
  "gameclock_max": 720,
  "direction": "up",
  "on_stop_behavior": "reset",
  "is_qtr": true,
  "is_time": true,
  "is_playclock": true,
  "is_downdistance": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Sport scoreboard preset not found |
| 500 | Internal server error |

---

### GET /api/sport-scoreboard-presets/id/{item_id}/

Get a sport scoreboard preset by ID.

**Endpoint:**
```
GET /api/sport-scoreboard-presets/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Preset ID to retrieve |

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "American Football Preset",
  "gameclock_max": 720,
  "direction": "down",
  "on_stop_behavior": "hold",
  "is_qtr": true,
  "is_time": true,
  "is_playclock": true,
  "is_downdistance": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Sport scoreboard preset not found |
| 500 | Internal server error |

---

### GET /api/sport-scoreboard-presets/

Get all sport scoreboard presets without pagination. Returns a simple list.

**Endpoint:**
```
GET /api/sport-scoreboard-presets/
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "American Football Preset",
    "gameclock_max": 720,
    "direction": "down",
    "on_stop_behavior": "hold",
    "is_qtr": true,
    "is_time": true,
    "is_playclock": true,
    "is_downdistance": true
  },
  {
    "id": 2,
    "title": "Basketball Preset",
    "gameclock_max": 600,
    "direction": "down",
    "on_stop_behavior": "hold",
    "is_qtr": false,
    "is_time": true,
    "is_playclock": false,
    "is_downdistance": false
  }
]
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

### GET /api/sport-scoreboard-presets/id/{preset_id}/sports

Get all sports associated with a specific preset.

**Endpoint:**
```
GET /api/sport-scoreboard-presets/id/{preset_id}/sports
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `preset_id` | integer | Yes | Preset ID |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "American Football",
    "description": "American football rules and gameplay",
    "scoreboard_preset_id": 1
  },
  {
    "id": 5,
    "title": "College Football",
    "description": "NCAA football rules",
    "scoreboard_preset_id": 1
  }
]
```

**Behavior:**
- Returns all sports that use the specified preset
- Returns empty array if no sports found

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

### DELETE /api/sport-scoreboard-presets/id/{model_id}

Delete a sport scoreboard preset by ID. Requires admin role.

**Endpoint:**
```
DELETE /api/sport-scoreboard-presets/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | Preset ID to delete |

**Response (200 OK):**
```json
{
  "detail": "Sport scoreboard preset 1 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | Sport scoreboard preset not found |
| 500 | Internal server error |

---

## Usage with Sports

Sport scoreboard presets can be assigned to sports via the `scoreboard_preset_id` field in the Sport schema. When a match is created for a sport with a preset, the gameclock and scoreboard will automatically use the preset's default values.

**Example: Assign preset to sport**

```json
PUT /api/sports/1/
{
  "title": "American Football",
  "description": "American football rules",
  "scoreboard_preset_id": 1
}
```

When creating a gameclock for a match in this sport, the following preset values will be applied automatically:
- `gameclock_max`: 720
- `direction`: "down"
- `on_stop_behavior`: "hold"
- `use_sport_preset`: true

Similarly, scoreboards will use the display configuration from the preset.
