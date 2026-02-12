# Scoreboards API

Manage scoreboard display settings for matches. Scoreboards control what elements are shown during game broadcasts (quarters, time, play clock, down/distance, logos, sponsors, etc.).

### Response Schemas

```typescript
interface ScoreboardSchema {
  id: number;
  is_qtr: boolean; // Show quarter display
  period_mode: "qtr" | "period" | "half" | "set" | "inning" | "custom"; // Canonical period label mode
  period_count: number; // Canonical number of periods (default: 4)
  period_labels_json: string[] | null; // Optional semantic labels for custom mode
  is_time: boolean; // Show game time display
  is_playclock: boolean; // Show play clock display
  is_downdistance: boolean; // Show down & distance display
  is_tournament_logo: boolean; // Show tournament logo
  is_main_sponsor: boolean; // Show main sponsor
  is_sponsor_line: boolean; // Show sponsor line
  is_match_sponsor_line: boolean; // Show match-specific sponsor line

  is_team_a_start_offense: boolean; // Team A starting offense indicator
  is_team_b_start_offense: boolean; // Team B starting offense indicator
  is_team_a_start_defense: boolean; // Team A starting defense indicator
  is_team_b_start_defense: boolean; // Team B starting defense indicator

  is_home_match_team_lower: boolean; // Lower home team display
  is_away_match_team_lower: boolean; // Lower away team display

  is_football_qb_full_stats_lower: boolean; // Show QB stats lower panel
  football_qb_full_stats_match_lower_id: number | null; // QB stats match ID reference
  is_match_player_lower: boolean; // Show player lower panel
  player_match_lower_id: number | null; // Player match ID reference

  team_a_game_color: string; // Team A hex color code (max 10 chars)
  team_b_game_color: string; // Team B hex color code (max 10 chars)
  use_team_a_game_color: boolean; // Use custom Team A color
  use_team_b_game_color: boolean; // Use custom Team B color

  team_a_game_title: string | null; // Custom Team A title (max 50 chars)
  team_b_game_title: string | null; // Custom Team B title (max 50 chars)
  use_team_a_game_title: boolean; // Use custom Team A title
  use_team_b_game_title: boolean; // Use custom Team B title

  team_a_game_logo: string | null; // Custom Team A logo path
  team_b_game_logo: string | null; // Custom Team B logo path
  use_team_a_game_logo: boolean; // Use custom Team A logo
  use_team_b_game_logo: boolean; // Use custom Team B logo

  scale_tournament_logo: number | null; // Tournament logo scale factor
  scale_main_sponsor: number | null; // Main sponsor scale factor
  scale_logo_a: number | null; // Team A logo scale factor
  scale_logo_b: number | null; // Team B logo scale factor

  is_flag: boolean | null; // Show flag indicator
  is_goal_team_a: boolean | null; // Team A goal indicator
  is_goal_team_b: boolean | null; // Team B goal indicator
  is_timeout_team_a: boolean | null; // Team A timeout indicator
  is_timeout_team_b: boolean | null; // Team B timeout indicator

  language_code: 'en' | 'ru' | null; // Scoreboard language code (default: 'en')

  match_id: number | null; // Associated match ID
}
```

---

### POST /api/scoreboards/

Create a new scoreboard configuration.

Capability enforcement note:
- If the match sport preset has `has_playclock=false`, backend forces `is_playclock=false`.
- If the match sport preset has `has_timeouts=false`, backend forces `is_timeout_team_a=false` and `is_timeout_team_b=false`.

**Endpoint:**
```
POST /api/scoreboards/
```

**Request Body:**
```json
{
  "is_qtr": true,
  "period_mode": "qtr",
  "period_count": 4,
  "period_labels_json": null,
  "is_time": true,
  "is_playclock": true,
  "is_downdistance": true,
  "is_tournament_logo": true,
  "is_main_sponsor": true,
  "is_sponsor_line": true,
  "language_code": "en",
  "team_a_game_color": "#c01c28",
  "team_b_game_color": "#1c71d8",
  "match_id": 123
}
```

**Request Schema:**
```typescript
interface ScoreboardSchemaCreate extends ScoreboardSchema {
  // All scoreboard fields, id is not required
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "is_qtr": true,
  "period_mode": "qtr",
  "period_count": 4,
  "period_labels_json": null,
  "is_time": true,
  "is_playclock": true,
  "is_downdistance": true,
  "is_tournament_logo": true,
  "is_main_sponsor": true,
  "is_sponsor_line": true,
  "is_match_sponsor_line": false,
  "language_code": "en",
  "team_a_game_color": "#c01c28",
  "team_b_game_color": "#1c71d8",
  "use_team_a_game_color": false,
  "use_team_b_game_color": false,
  "match_id": 123
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Bad request - validation error |
| 500 | Internal server error |

---

### PUT /api/scoreboards/{item_id}/

Update a scoreboard by ID.

Capability enforcement note:
- Backend applies the same capability guards during update, so unsupported features cannot be effectively enabled.

**Endpoint:**
```
PUT /api/scoreboards/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Scoreboard ID to update |

**Request Body:**
```json
{
  "is_qtr": false,
  "period_mode": "half",
  "period_count": 2,
  "use_team_a_game_color": true
}
```

**Request Schema:**
```typescript
interface ScoreboardSchemaUpdate {
  // All scoreboard fields are optional
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "is_qtr": false,
  "period_mode": "half",
  "period_count": 2,
  "period_labels_json": null,
  "is_time": true,
  "use_team_a_game_color": true,
  "team_a_game_color": "#c01c28"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Scoreboard not found |
| 500 | Internal server error |

---

### PUT /api/scoreboards/id/{item_id}/

Update a scoreboard by ID with JSONResponse format.

**Endpoint:**
```
PUT /api/scoreboards/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Scoreboard ID to update |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "is_qtr": true,
    "period_mode": "qtr",
    "period_count": 4,
    "period_labels_json": null,
    "is_time": true
  },
  "status_code": 200,
  "success": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Scoreboard not found |
| 500 | Internal server error |

---

### GET /api/scoreboards/match/id/{match_id}

Get scoreboard by match ID.

**Endpoint:**
```
GET /api/scoreboards/match/id/{match_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID |

**Response (200 OK):**
```json
{
  "id": 1,
  "is_qtr": true,
  "period_mode": "qtr",
  "period_count": 4,
  "period_labels_json": null,
  "is_time": true,
  "match_id": 123
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Scoreboard not found for this match |
| 500 | Internal server error |

---

### GET /api/scoreboards/id/{item_id}/

Get a scoreboard by ID.

**Endpoint:**
```
GET /api/scoreboards/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Scoreboard ID to retrieve |

**Response (200 OK):**
```json
{
  "id": 1,
  "is_qtr": true,
  "period_mode": "qtr",
  "period_count": 4,
  "period_labels_json": null,
  "is_time": true,
  "match_id": 123
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Scoreboard not found |
| 500 | Internal server error |

---

### GET /api/scoreboards/matchdata/id/{matchdata_id}

Get scoreboard by matchdata ID.

**Endpoint:**
```
GET /api/scoreboards/matchdata/id/{matchdata_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `matchdata_id` | integer | Yes | MatchData ID |

**Response (200 OK):**
```json
{
  "id": 1,
  "is_qtr": true,
  "period_mode": "qtr",
  "period_count": 4,
  "period_labels_json": null,
  "is_time": true,
  "match_id": 123
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Scoreboard not found for this matchdata |
| 500 | Internal server error |

---

### DELETE /api/scoreboards/id/{model_id}

Delete a scoreboard by ID. Requires admin role.

**Endpoint:**
```
DELETE /api/scoreboards/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | Scoreboard ID to delete |

**Response (200 OK):**
```json
{
  "detail": "Scoreboard 1 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | Scoreboard not found |
| 500 | Internal server error |

---
