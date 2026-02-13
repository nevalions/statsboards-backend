# Sport Scoreboard Presets API

Manage sport-specific scoreboard and gameclock presets. Presets define default configurations for different sports, including gameclock settings (direction, behavior) and scoreboard display options.

### Response Schemas

```typescript
interface SportScoreboardPresetSchema {
  id: number;
  title: string; // Max 255 characters
  gameclock_max: number | null; // Maximum gameclock time in seconds, default 720
  initial_time_mode: "max" | "zero" | "min"; // Initial gameclock strategy, default "max"
  initial_time_min_seconds: number | null; // Required when initial_time_mode="min"
  period_clock_variant: "per_period" | "cumulative"; // Period transition clock strategy, default "per_period"
  direction: string; // Clock direction: "down" or "up" (default: "down")
  on_stop_behavior: string; // Behavior when stopped: "hold" or "reset" (default: "hold")
  has_playclock: boolean; // Sport supports playclock entities (default: true)
  has_timeouts: boolean; // Sport supports timeout indicators (default: true)
  is_qtr: boolean; // Show quarter indicator (default: true)
  is_time: boolean; // Show time display (default: true)
  is_playclock: boolean; // Show playclock (default: true)
  is_downdistance: boolean; // Show down and distance (default: true)
  has_timeouts: boolean; // Sport supports timeouts (default: true)
  has_playclock: boolean; // Sport uses playclock rules (default: true)
  period_mode: "qtr" | "period" | "half" | "set" | "inning" | "custom"; // Label mode (default: "qtr")
  period_count: number; // Canonical number of periods (default: 4)
  period_labels_json: string[] | null; // Optional custom semantic keys, used with period_mode="custom" (example: "period.q1")
  default_playclock_seconds: number | null; // Optional playclock default for the sport
  quick_score_deltas: number[]; // Ordered score button values (default: [6,3,2,1,-1])
}

interface SportScoreboardPresetSchemaCreate {
  title: string; // Max 255 characters
  gameclock_max: number | null; // Optional max time in seconds, default 720
  initial_time_mode: "max" | "zero" | "min"; // Optional initial gameclock strategy, default "max"
  initial_time_min_seconds: number | null; // Optional, required when initial_time_mode="min"
  period_clock_variant: "per_period" | "cumulative"; // Optional, defaults to "per_period"
  direction: string; // Clock direction: "down" or "up" (default: "down")
  on_stop_behavior: string; // Behavior when stopped: "hold" or "reset" (default: "hold")
  has_playclock: boolean; // Optional, defaults to true
  has_timeouts: boolean; // Optional, defaults to true
  is_qtr: boolean; // Show quarter indicator, defaults to true
  is_time: boolean; // Show time display, defaults to true
  is_playclock: boolean; // Show playclock, defaults to true
  is_downdistance: boolean; // Show down and distance, defaults to true
  has_timeouts: boolean; // Sport supports timeouts, defaults to true
  has_playclock: boolean; // Sport uses playclock rules, defaults to true
  period_mode: "qtr" | "period" | "half" | "set" | "inning" | "custom"; // Defaults to "qtr"
  period_count: number; // Canonical number of periods, defaults to 4
  period_labels_json: string[] | null; // Optional custom semantic keys (not translated display text)
  default_playclock_seconds: number | null; // Optional playclock default
  quick_score_deltas: number[]; // Optional; defaults to [6,3,2,1,-1]
}

interface SportScoreboardPresetSchemaUpdate {
  title: string | null; // Optional - Max 255 characters
  gameclock_max: number | null; // Optional max time in seconds
  initial_time_mode: "max" | "zero" | "min" | null; // Optional initial gameclock strategy
  initial_time_min_seconds: number | null; // Optional, required when initial_time_mode="min"
  period_clock_variant: "per_period" | "cumulative" | null; // Optional period transition clock strategy
  direction: string | null; // Optional clock direction: "down" or "up"
  on_stop_behavior: string | null; // Optional behavior when stopped: "hold" or "reset"
  has_playclock: boolean | null; // Optional capability flag
  has_timeouts: boolean | null; // Optional capability flag
  is_qtr: boolean | null; // Optional quarter indicator
  is_time: boolean | null; // Optional time display
  is_playclock: boolean | null; // Optional playclock
  is_downdistance: boolean | null; // Optional down and distance
  has_timeouts: boolean | null; // Optional sport timeout capability
  has_playclock: boolean | null; // Optional sport playclock capability
  period_mode: "qtr" | "period" | "half" | "set" | "inning" | "custom" | null; // Optional period mode
  period_count: number | null; // Optional period count
  period_labels_json: string[] | null; // Optional semantic keys (or null)
  default_playclock_seconds: number | null; // Optional playclock default (or null)
  quick_score_deltas: number[] | null; // Optional ordered score values (or null in partial update payload)
}
```

### Initial Gameclock Strategy (seconds)

- All time values are in seconds.
- `gameclock_max` is the configured upper bound.
- `initial_time_mode` determines the initial `gameclock` value for newly created match gameclocks:
  - `max`: start at `gameclock_max`
  - `zero`: start at `0`
  - `min`: start at `initial_time_min_seconds`
- `initial_time_min_seconds` is required when `initial_time_mode="min"`.
- `period_clock_variant` controls max-time handling when period changes:
  - `per_period` (default): effective max remains `gameclock_max`
  - `cumulative`: effective max becomes `gameclock_max * current_period_index`
- `period_count` is required and must be >= 1.
- when `period_mode="custom"`, `period_count` must equal `period_labels_json.length`.
- `quick_score_deltas` must be a non-empty ordered list of integers.
- `quick_score_deltas` cannot contain `0`.
- `quick_score_deltas` has max length `10` and allowed range `-100..100`.
- Final initial value is clamped to a non-negative range:
  - when `gameclock_max` is set: `0 <= gameclock <= gameclock_max`
  - when `gameclock_max` is `null`: `gameclock >= 0`

Soccer example (`period_clock_variant="cumulative"`, 45-minute halves):
- Base `gameclock_max = 2700`
- Half 1 (`period.1`) effective max: `2700` (45:00)
- Half 2 (`period.2`) effective max: `5400` (90:00)

Example payloads:

```json
{
  "title": "Football (max)",
  "gameclock_max": 900,
  "initial_time_mode": "max",
  "initial_time_min_seconds": null
}
```

```json
{
  "title": "Countdown from zero",
  "gameclock_max": 900,
  "initial_time_mode": "zero",
  "initial_time_min_seconds": null
}
```

```json
{
  "title": "Soccer half",
  "gameclock_max": 3600,
  "initial_time_mode": "min",
  "initial_time_min_seconds": 2700
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
  "initial_time_mode": "max",
  "initial_time_min_seconds": null,
  "period_clock_variant": "per_period",
  "direction": "down",
  "on_stop_behavior": "hold",
  "has_playclock": true,
  "has_timeouts": true,
  "is_qtr": true,
  "is_time": true,
  "is_playclock": true,
  "is_downdistance": true,
  "has_timeouts": true,
  "has_playclock": true,
  "period_mode": "qtr",
  "period_count": 4,
  "period_labels_json": null,
  "default_playclock_seconds": 40,
  "quick_score_deltas": [6, 3, 2, 1, -1]
}
```

**Request Schema:**
```typescript
interface SportScoreboardPresetSchemaCreate {
  title: string; // Max 255 characters
  gameclock_max: number | null; // Optional max time in seconds
  initial_time_mode: "max" | "zero" | "min";
  initial_time_min_seconds: number | null;
  period_clock_variant: "per_period" | "cumulative";
  direction: string; // Clock direction: "down" or "up"
  on_stop_behavior: string; // Behavior when stopped: "hold" or "reset"
  has_playclock: boolean; // Sport supports playclock entities
  has_timeouts: boolean; // Sport supports timeout indicators
  is_qtr: boolean; // Show quarter indicator
  is_time: boolean; // Show time display
  is_playclock: boolean; // Show playclock
  is_downdistance: boolean; // Show down and distance
  has_timeouts: boolean; // Sport supports timeouts
  has_playclock: boolean; // Sport uses playclock rules
  period_mode: "qtr" | "period" | "half" | "set" | "inning" | "custom";
  period_count: number;
  period_labels_json: string[] | null;
  default_playclock_seconds: number | null;
  quick_score_deltas: number[];
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "American Football Preset",
  "gameclock_max": 720,
  "initial_time_mode": "max",
  "initial_time_min_seconds": null,
  "period_clock_variant": "per_period",
  "direction": "down",
  "on_stop_behavior": "hold",
  "has_playclock": true,
  "has_timeouts": true,
  "is_qtr": true,
  "is_time": true,
  "is_playclock": true,
  "is_downdistance": true,
  "has_timeouts": true,
  "has_playclock": true,
  "period_mode": "qtr",
  "period_count": 4,
  "period_labels_json": null,
  "default_playclock_seconds": 40,
  "quick_score_deltas": [6, 3, 2, 1, -1]
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
  "period_clock_variant": "cumulative",
  "direction": "up",
  "on_stop_behavior": "reset",
  "period_mode": "custom",
  "period_count": 2,
  "period_labels_json": ["period.leg_1", "period.leg_2"],
  "default_playclock_seconds": 30,
  "quick_score_deltas": [1, -1]
}
```

**Request Schema:**
```typescript
interface SportScoreboardPresetSchemaUpdate {
  title: string | null; // Optional - Max 255 characters
  gameclock_max: number | null; // Optional max time in seconds
  initial_time_mode: "max" | "zero" | "min" | null;
  initial_time_min_seconds: number | null;
  period_clock_variant: "per_period" | "cumulative" | null;
  direction: string | null; // Optional clock direction: "down" or "up"
  on_stop_behavior: string | null; // Optional behavior when stopped: "hold" or "reset"
  has_playclock: boolean | null; // Optional capability flag
  has_timeouts: boolean | null; // Optional capability flag
  is_qtr: boolean | null; // Optional quarter indicator
  is_time: boolean | null; // Optional time display
  is_playclock: boolean | null; // Optional playclock
  is_downdistance: boolean | null; // Optional down and distance
  has_timeouts: boolean | null; // Optional sport timeout capability
  has_playclock: boolean | null; // Optional sport playclock capability
  period_mode: "qtr" | "period" | "half" | "set" | "inning" | "custom" | null;
  period_count: number | null;
  period_labels_json: string[] | null;
  default_playclock_seconds: number | null;
  quick_score_deltas: number[] | null;
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "American Football Preset - Updated",
  "gameclock_max": 720,
  "initial_time_mode": "max",
  "initial_time_min_seconds": null,
  "period_clock_variant": "cumulative",
  "direction": "up",
  "on_stop_behavior": "reset",
  "has_playclock": true,
  "has_timeouts": true,
  "is_qtr": true,
  "is_time": true,
  "is_playclock": true,
  "is_downdistance": true,
  "has_timeouts": true,
  "has_playclock": true,
  "period_mode": "custom",
  "period_count": 2,
  "period_labels_json": ["period.leg_1", "period.leg_2"],
  "default_playclock_seconds": 30,
  "quick_score_deltas": [1, -1]
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
  "initial_time_mode": "max",
  "initial_time_min_seconds": null,
  "period_clock_variant": "per_period",
  "direction": "down",
  "on_stop_behavior": "hold",
  "has_playclock": true,
  "has_timeouts": true,
  "is_qtr": true,
  "is_time": true,
  "is_playclock": true,
  "is_downdistance": true,
  "has_timeouts": true,
  "has_playclock": true,
  "period_mode": "qtr",
  "period_count": 4,
  "period_labels_json": null,
  "default_playclock_seconds": 40,
  "quick_score_deltas": [6, 3, 2, 1, -1]
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
    "initial_time_mode": "max",
    "initial_time_min_seconds": null,
    "period_clock_variant": "per_period",
    "direction": "down",
    "on_stop_behavior": "hold",
    "has_playclock": true,
    "has_timeouts": true,
    "is_qtr": true,
    "is_time": true,
    "is_playclock": true,
    "is_downdistance": true,
    "has_timeouts": true,
    "has_playclock": true,
    "period_mode": "qtr",
    "period_count": 4,
    "period_labels_json": null,
    "default_playclock_seconds": 40,
    "quick_score_deltas": [6, 3, 2, 1, -1]
  },
  {
    "id": 2,
    "title": "Basketball Preset",
    "gameclock_max": 600,
    "initial_time_mode": "max",
    "initial_time_min_seconds": null,
    "period_clock_variant": "per_period",
    "direction": "down",
    "on_stop_behavior": "hold",
    "has_playclock": false,
    "has_timeouts": true,
    "is_qtr": false,
    "is_time": true,
    "is_playclock": false,
    "is_downdistance": false,
    "has_timeouts": true,
    "has_playclock": true,
    "period_mode": "half",
    "period_count": 2,
    "period_labels_json": null,
    "default_playclock_seconds": 24,
    "quick_score_deltas": [2, 1, -1]
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

Capability flags are enforced server-side:
- `has_playclock=false` prevents playclock auto-creation/fetch bootstrap for the match.
- `has_timeouts=false` forces timeout indicators on scoreboards to stay `false`.

Preset updates are also propagated to opted-in match resources (`use_sport_preset=true`):
- Scoreboards receive updated preset display fields and capability reconciliation.
- Gameclocks receive updated period config defaults (`gameclock_max`, `direction`, `on_stop_behavior`).
- For `period_clock_variant="cumulative"`, propagated gameclocks use period-aware effective max based on current match period (`period_key` / `qtr`).
- If `has_playclock` flips from `true` to `false`, existing playclock rows for opted-in matches are safely deactivated (`playclock=null`, `playclock_status="stopped"`, `started_at_ms=null`).
- If `has_timeouts` flips from `true` to `false`, timeout indicators are deterministically set to `false`.
- Opt-out matches (`use_sport_preset=false`) are not modified by preset propagation.

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
- `gameclock`: chosen by `initial_time_mode` (`max`, `zero`, `min`)
- `gameclock_max`: 720
- `direction`: "down"
- `on_stop_behavior`: "hold"
- `use_sport_preset`: true

Similarly, scoreboards will use the display configuration from the preset.

## I18n Boundary

- Backend responses return machine-friendly keys/codes (for example `period_mode` and `period_labels_json`).
- Frontend is responsible for mapping those keys to localized scoreboard display labels.
- Do not store or return translated scoreboard display strings from backend preset payloads.
