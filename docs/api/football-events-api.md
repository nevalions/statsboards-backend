# Football Events API

### GET /api/football_event/matches/{match_id}/events-with-players/

Get all football events for a match with all 17 player references pre-populated with full player data. This endpoint eliminates the O(n*m) frontend join complexity by returning player data embedded in each event.

**Endpoint:**
```
GET /api/football_event/matches/{match_id}/events-with-players/
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID |

**Response (200 OK):**

```json
{
  "match_id": 123,
  "events": [
    {
      "id": 1,
      "match_id": 123,
      "event_number": 1,
      "event_qtr": 1,
      "ball_on": 25,
      "ball_moved_to": 37,
      "ball_picked_on": null,
      "ball_kicked_to": null,
      "ball_returned_to": null,
      "ball_picked_on_fumble": null,
      "ball_returned_to_on_fumble": null,
      "distance_on_offence": 12,
      "offense_team": 1,
      "event_qb": 456,
      "event_down": 1,
      "event_distance": 10,
      "event_hash": "abc123",
      "play_direction": "left",
      "event_strong_side": "left",
      "play_type": "pass",
      "play_result": "pass_completed",
      "score_result": null,
      "is_fumble": false,
      "is_fumble_recovered": false,

      "qb": {
        "id": 456,
        "player_id": 789,
        "player": {
          "id": 789,
          "first_name": "Tom",
          "second_name": "Brady",
          "person_photo_url": "/static/uploads/persons/photos/789.jpg"
        },
        "position": {
          "id": 10,
          "name": "Quarterback"
        },
        "team": {
          "id": 1,
          "name": "Team A",
          "logo_url": "/static/uploads/teams/logos/1.jpg"
        },
        "match_number": "12"
      },
      "run_player": null,
      "pass_received_player": {
        "id": 457,
        "player_id": 790,
        "player": {
          "id": 790,
          "first_name": "Julian",
          "second_name": "Edelman",
          "person_photo_url": "/static/uploads/persons/photos/790.jpg"
        },
        "position": {
          "id": 15,
          "name": "Wide Receiver"
        },
        "team": {
          "id": 1,
          "name": "Team A",
          "logo_url": "/static/uploads/teams/logos/1.jpg"
        },
        "match_number": "11"
      },
      "pass_dropped_player": null,
      "pass_deflected_player": null,
      "pass_intercepted_player": null,
      "fumble_player": null,
      "fumble_recovered_player": null,
      "tackle_player": {
        "id": 460,
        "player_id": 793,
        "player": {
          "id": 793,
          "first_name": "Von",
          "second_name": "Miller",
          "person_photo_url": "/static/uploads/persons/photos/793.jpg"
        },
        "position": {
          "id": 20,
          "name": "Linebacker"
        },
        "team": {
          "id": 2,
          "name": "Team B",
          "logo_url": "/static/uploads/teams/logos/2.jpg"
        },
        "match_number": "58"
      },
      "assist_tackle_player": null,
      "sack_player": null,
      "score_player": null,
      "defence_score_player": null,
      "kick_player": null,
      "kickoff_player": null,
      "return_player": null,
      "pat_one_player": null,
      "flagged_player": null,
      "punt_player": null
    }
  ]
}
```

**Response Schema:**

```typescript
interface FootballEventsWithPlayersResponse {
  match_id: number;
  events: FootballEventWithPlayers[];
}

interface FootballEventWithPlayers {
  id: number;
  match_id: number;
  event_number: number | null;
  event_qtr: number | null;
  ball_on: number | null;
  ball_moved_to: number | null;
  ball_picked_on: number | null;
  ball_kicked_to: number | null;
  ball_returned_to: number | null;
  ball_picked_on_fumble: number | null;
  ball_returned_to_on_fumble: number | null;
  distance_on_offence: number | null;
  offense_team: number | null;
  event_qb: number | null;
  event_down: number | null;
  event_distance: number | null;
  event_hash: string | null;
  play_direction: string | null;
  event_strong_side: string | null;
  play_type: string | null;
  play_result: string | null;
  score_result: string | null;
  is_fumble: boolean | null;
  is_fumble_recovered: boolean | null;

  // Player references with full data (all optional)
  qb: PlayerMatchDetail | null;
  run_player: PlayerMatchDetail | null;
  pass_received_player: PlayerMatchDetail | null;
  pass_dropped_player: PlayerMatchDetail | null;
  pass_deflected_player: PlayerMatchDetail | null;
  pass_intercepted_player: PlayerMatchDetail | null;
  fumble_player: PlayerMatchDetail | null;
  fumble_recovered_player: PlayerMatchDetail | null;
  tackle_player: PlayerMatchDetail | null;
  assist_tackle_player: PlayerMatchDetail | null;
  sack_player: PlayerMatchDetail | null;
  score_player: PlayerMatchDetail | null;
  defence_score_player: PlayerMatchDetail | null;
  kick_player: PlayerMatchDetail | null;
  kickoff_player: PlayerMatchDetail | null;
  return_player: PlayerMatchDetail | null;
  pat_one_player: PlayerMatchDetail | null;
  flagged_player: PlayerMatchDetail | null;
  punt_player: PlayerMatchDetail | null;
}

interface PlayerMatchDetail {
  id: number;
  player_id: number | null;
  player: {
    id: number;
    first_name: string;
    second_name: string;
    person_photo_url: string | null;
  } | null;
  position: {
    id: number;
    name: string;
  } | null;
  team: {
    id: number;
    name: string;
    logo_url: string | null;
  } | null;
  match_number: string;
}
```

**Performance Benefits:**

This endpoint provides significant performance improvements over frontend-only joins:

- **Single optimized query** with selectinload (no N+1 problem)
- **Pre-populated player data** eliminates 1,600+ frontend lookups (100 events × 16 players)
- **Expected response time**: < 50ms vs frontend O(n*m) > 200ms
- **Reduced client complexity**: No need for complex NgRx selectors

**Use Case:**

Use this endpoint when displaying football plays in scoreboard or play-by-play view where player information (name, photo, position, team) is needed for each event.

---

### POST /api/football_event/

Create a new football event.

**Endpoint:**
```
POST /api/football_event/
```

**Request Body:**
```json
{
  "match_id": 123,
  "event_number": 1,
  "event_qtr": 1,
  "ball_on": 25,
  "ball_moved_to": 37,
  "offense_team": 1,
  "event_qb": 456,
  "event_down": 1,
  "event_distance": 10,
  "play_type": "pass",
  "play_result": "pass_completed"
}
```

**Request Schema:**
```typescript
interface FootballEventSchemaCreate {
  match_id: number | null; // Optional associated match ID

  event_number: number | null; // Event sequence number
  event_qtr: number | null; // Quarter (1, 2, 3, 4)
  ball_on: number | null; // Ball position (yard line)
  ball_moved_to: number | null; // Ball moved to position
  ball_picked_on: number | null; // Ball picked up position
  ball_kicked_to: number | null; // Kick destination
  ball_returned_to: number | null; // Return destination
  ball_picked_on_fumble: number | null; // Fumble pickup position
  ball_returned_to_on_fumble: number | null; // Fumble return position
  offense_team: number | null; // Team ID on offense

  event_qb: number | null; // Quarterback player ID
  event_down: number | null; // Down (1, 2, 3, 4)
  event_distance: number | null; // Distance to gain
  distance_on_offence: number | null; // Distance gained on offense

  event_hash: string | null; // Event hash (max 150 chars)
  play_direction: string | null; // "left", "right", "middle" (max 150 chars)
  event_strong_side: string | null; // "left", "right" (max 150 chars)
  play_type: string | null; // "run", "pass", "kick", "punt" (max 150 chars)
  play_result: string | null; // "gain", "loss", "incomplete", "interception" (max 150 chars)
  score_result: string | null; // "touchdown", "field_goal", "none" (max 150 chars)

  is_fumble: boolean | null; // Fumble occurred
  is_fumble_recovered: boolean | null; // Fumble recovered

  // Player references (all optional)
  run_player: number | null; // Running back player ID
  pass_received_player: number | null; // Receiver player ID
  pass_dropped_player: number | null; // Dropped pass player ID
  pass_deflected_player: number | null; // Deflected pass player ID
  pass_intercepted_player: number | null; // Interception player ID
  fumble_player: number | null; // Fumble player ID
  fumble_recovered_player: number | null; // Fumble recovery player ID
  tackle_player: number | null; // Tackle player ID
  assist_tackle_player: number | null; // Assist tackle player ID
  sack_player: number | null; // Sack player ID
  score_player: number | null; // Scoring player ID
  defence_score_player: number | null; // Defensive score player ID
  kickoff_player: number | null; // Kickoff player ID
  return_player: number | null; // Return player ID
  pat_one_player: number | null; // PAT kicker player ID
  flagged_player: number | null; // Flagged player ID
  kick_player: number | null; // Kick player ID
  punt_player: number | null; // Punt player ID
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "match_id": 123,
  "event_number": 1,
  "event_qtr": 1,
  "ball_on": 25,
  "ball_moved_to": 37,
  "play_type": "pass",
  "play_result": "pass_completed"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

### PUT /api/football_event/{item_id}/

Update a football event by ID.

**Endpoint:**
```
PUT /api/football_event/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Football Event ID to update |

**Request Body:**
```json
{
  "event_down": 2,
  "ball_moved_to": 42,
  "play_result": "incomplete"
}
```

**Request Schema:**
```typescript
interface FootballEventSchemaUpdate {
  // All fields from FootballEventSchemaCreate are optional
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "match_id": 123,
  "event_number": 1,
  "event_qtr": 1,
  "ball_on": 25,
  "ball_moved_to": 42,
  "event_down": 2,
  "play_result": "incomplete"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Football event not found |
| 500 | Internal server error |

---

### GET /api/football_event/match_id/{match_id}/

Get all football events for a specific match.

**Endpoint:**
```
GET /api/football_event/match_id/{match_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "match_id": 123,
    "event_number": 1,
    "event_qtr": 1,
    "ball_on": 25,
    "play_type": "pass",
    "play_result": "pass_completed"
  },
  {
    "id": 2,
    "match_id": 123,
    "event_number": 2,
    "event_qtr": 1,
    "ball_on": 37,
    "play_type": "run",
    "play_result": "gain"
  }
]
```

**Behavior:**
- Returns all football events for the specified match
- Ordered by event number ascending
- Returns empty array if no events found

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

### DELETE /api/football_event/id/{model_id}

Delete a football event by ID. Requires admin role.

**Endpoint:**
```
DELETE /api/football_event/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | Football Event ID to delete |

**Response (200 OK):**
```json
{
  "detail": "FootballEvent 1 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | Football Event not found |
| 500 | Internal server error |

---
