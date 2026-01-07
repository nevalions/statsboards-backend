# Backend API Documentation

Frontend integration guide for StatsBoards Backend APIs and WebSocket endpoints.

## Table of Contents

- [Player Search API](#player-search-api)
- [Teams in Tournament API](#teams-in-tournament-api)
- [Match Stats API](#match-stats-api)
- [WebSocket Message Formats](#websocket-message-formats)
- [Player Match API](#player-match-api)
- [Team Rosters API](#team-rosters-api)
- [Football Events API](#football-events-api)
- [Error Responses](#error-responses)
- [Integration Examples](#integration-examples)

---

## Player Search API

### GET /api/players/paginated/details

Search players by sport with pagination, optional team filter, and name search. Returns players with person data and their team/position associations.

**Endpoint:**
```
GET /api/players/paginated/details
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|----------|-------------|
| `sport_id` | integer | Yes | - | Sport ID to filter players |
| `team_id` | integer | No | - | Team ID to filter players (optional) |
| `search` | string | No | - | Search query for person names (first_name OR second_name) |
| `page` | integer | No | 1 | Page number (1-based) |
| `items_per_page` | integer | No | 20 | Items per page (max 100) |
| `order_by` | string | No | "id" | First sort column |
| `order_by_two` | string | No | "id" | Second sort column |
| `ascending` | boolean | No | true | Sort order (true=asc, false=desc) |

**Response (200 OK):**

```json
{
  "data": [
    {
      "id": 1,
      "sport_id": 1,
      "person_id": 123,
      "player_eesl_id": 98765,
      "first_name": "Ivan",
      "second_name": "Ivanov",
      "player_team_tournaments": [
        {
          "id": 10,
          "player_team_tournament_eesl_id": 12345,
          "player_number": "12",
          "team_id": 5,
          "team_title": "Team A",
          "position_id": 3,
          "position_title": "Quarterback",
          "tournament_id": 2
        }
      ]
    }
  ],
  "metadata": {
    "page": 1,
    "items_per_page": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

**Response Schema:**

```typescript
interface PaginatedPlayerWithDetailsResponse {
  data: PlayerWithDetails[];
  metadata: PaginationMetadata;
}

interface PlayerWithDetails {
  id: number;
  sport_id: number | null;
  person_id: number | null;
  player_eesl_id: number | null;
  first_name: string | null;
  second_name: string | null;
  player_team_tournaments: PlayerTeamTournamentInfo[];
}

interface PlayerTeamTournamentInfo {
  id: number;
  player_team_tournament_eesl_id: number | null;
  player_number: string;
  team_id: number | null;
  team_title: string | null;
  position_id: number | null;
  position_title: string | null;
  tournament_id: number | null;
}

interface PaginationMetadata {
  page: number;
  items_per_page: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}
```

**Search Behavior:**

- Search is case-insensitive and uses ICU collation (`en-US-x-icu`) for international text support
- Searches both `first_name` and `second_name` fields with OR logic
- Pattern matching: `%query%` (matches anywhere in the name)
- Empty `search` parameter returns all players filtered by sport_id (and team_id if provided)

**Examples:**

1. **Get all players in sport:**
```
GET /api/players/paginated/details?sport_id=1&page=1&items_per_page=20
```

2. **Search players by name:**
```
GET /api/players/paginated/details?sport_id=1&search=Ivan&page=1&items_per_page=20
```

3. **Filter by team:**
```
GET /api/players/paginated/details?sport_id=1&team_id=5&page=1&items_per_page=20
```

4. **Search and filter by team:**
```
GET /api/players/paginated/details?sport_id=1&team_id=5&search=Ivan&page=1&items_per_page=20
```

5. **Sort by first name:**
```
GET /api/players/paginated/details?sport_id=1&order_by=id&order_by_two=person_id&ascending=true
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - players returned |
| 400 | Bad Request - invalid query parameters |
| 404 | Not Found - sport_id doesn't exist |
| 500 | Internal Server Error - server error |

---

## Teams in Tournament API

### GET /api/tournaments/id/{tournament_id}/teams/paginated

Search and paginate teams in a specific tournament. Supports search by team title, pagination, and ordering.

**Endpoint:**
```
GET /api/tournaments/id/{tournament_id}/teams/paginated
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tournament_id` | integer | Yes | Tournament ID |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|----------|-------------|
| `search` | string | No | - | Search query for team title |
| `page` | integer | No | 1 | Page number (1-based) |
| `items_per_page` | integer | No | 20 | Items per page (max 100) |
| `order_by` | string | No | "title" | First sort column |
| `order_by_two` | string | No | "id" | Second sort column |
| `ascending` | boolean | No | true | Sort order (true=asc, false=desc) |

**Response (200 OK):**

```json
{
  "data": [
    {
      "id": 1,
      "team_eesl_id": 12345,
      "title": "Manchester United",
      "city": "Manchester",
      "description": "Premier League football club",
      "team_logo_url": "https://example.com/logos/manchester-united.png",
      "team_logo_icon_url": "https://example.com/icons/manchester-united-icon.png",
      "team_logo_web_url": "https://example.com/web/manchester-united.png",
      "team_color": "#DA291C",
      "sponsor_line_id": null,
      "main_sponsor_id": 5,
      "sport_id": 1
    }
  ],
  "metadata": {
    "page": 1,
    "items_per_page": 20,
    "total_items": 25,
    "total_pages": 2,
    "has_next": true,
    "has_previous": false
  }
}
```

**Response Schema:**

```typescript
interface PaginatedTeamResponse {
  data: Team[];
  metadata: PaginationMetadata;
}

interface Team {
  id: number;
  team_eesl_id: number | null;
  title: string;
  city: string | null;
  description: string | null;
  team_logo_url: string | null;
  team_logo_icon_url: string | null;
  team_logo_web_url: string | null;
  team_color: string;
  sponsor_line_id: number | null;
  main_sponsor_id: number | null;
  sport_id: number;
}

interface PaginationMetadata {
  page: number;
  items_per_page: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}
```

**Search Behavior:**

- Search is case-insensitive and uses ICU collation (`en-US-x-icu`) for international text support
- Searches `title` field with pattern matching
- Pattern matching: `%query%` (matches anywhere in team title)
- Empty `search` parameter returns all teams in the tournament
- Only teams that are associated with the tournament via `team_tournament` table are returned

**Examples:**

1. **Get all teams in tournament with pagination:**
```
GET /api/tournaments/id/1/teams/paginated?page=1&items_per_page=20
```

2. **Search teams by title:**
```
GET /api/tournaments/id/1/teams/paginated?search=Manchester&page=1&items_per_page=20
```

3. **Get second page with custom ordering:**
```
GET /api/tournaments/id/1/teams/paginated?page=2&items_per_page=10&order_by=title&order_by_two=id&ascending=false
```

4. **Search and paginate:**
```
GET /api/tournaments/id/1/teams/paginated?search=United&page=1&items_per_page=20&order_by=title&ascending=true
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - teams returned |
| 400 | Bad Request - invalid query parameters |
| 404 | Not Found - tournament_id doesn't exist |
| 500 | Internal Server Error - server error |

---

## Match Stats API

### WebSocket Endpoint: Real-time Match Statistics

#### Connection

```typescript
const ws = new WebSocket('ws://localhost:9000/api/matches/ws/matches/{match_id}/stats');
```

#### Message Flow

1. **Client connects** to WebSocket endpoint
2. **Server sends** `full_stats_update` immediately on connection
3. **Client receives** `stats_update` messages when stats change
4. **Client can send** `stats_update` messages to update stats (with conflict resolution)

#### Server-Sent Messages

##### 1. Full Stats Update

Sent immediately after client connects.

```json
{
  "type": "full_stats_update",
  "match_id": 123,
  "stats": {
    "match_id": 123,
    "team_a": {
      "id": 1,
      "team_stats": {
        "id": 1,
        "offence_yards": 250,
        "pass_att": 20,
        "run_att": 30,
        "avg_yards_per_att": 5.0,
        "pass_yards": 150,
        "run_yards": 100,
        "lost_yards": 10,
        "flag_yards": -15,
        "third_down_attempts": 8,
        "third_down_conversions": 3,
        "fourth_down_attempts": 2,
        "fourth_down_conversions": 1,
        "first_down_gained": 15,
        "turnovers": 2
      },
      "offense_stats": {
        "456": {
          "id": 456,
          "pass_attempts": 10,
          "pass_received": 8,
          "pass_yards": 120,
          "pass_td": 1,
          "run_attempts": 5,
          "run_yards": 40,
          "run_avr": 8.0,
          "run_td": 0,
          "fumble": 0
        }
      },
      "qb_stats": {
        "789": {
          "id": 789,
          "passes": 15,
          "passes_completed": 10,
          "pass_yards": 150,
          "pass_td": 2,
          "pass_avr": 66.67,
          "run_attempts": 2,
          "run_yards": 10,
          "run_td": 0,
          "run_avr": 5.0,
          "fumble": 0,
          "interception": 1,
          "qb_rating": 85.5
        }
      },
      "defense_stats": {
        "101": {
          "id": 101,
          "tackles": 5,
          "assist_tackles": 3,
          "sacks": 1,
          "interceptions": 1,
          "fumble_recoveries": 1,
          "flags": 0
        }
      }
    },
    "team_b": {
      "id": 2,
      "team_stats": { /* same structure as team_a */ },
      "offense_stats": { /* same structure as team_a */ },
      "qb_stats": { /* same structure as team_a */ },
      "defense_stats": { /* same structure as team_a */ }
    }
  },
  "server_timestamp": "2026-01-02T17:30:00.123456"
}
```

##### 2. Stats Update

Broadcast when any client updates stats (or server-side changes occur).

```json
{
  "type": "stats_update",
  "match_id": 123,
  "stats": {
    "match_id": 123,
    "team_a": { /* full stats structure */ },
    "team_b": { /* full stats structure */ }
  },
  "server_timestamp": "2026-01-02T17:31:00.123456"
}
```

##### 3. Stats Sync (Conflict Resolution)

Sent when client's update is rejected due to conflict (server has newer data).

```json
{
  "type": "stats_sync",
  "match_id": 123,
  "stats": {
    "match_id": 123,
    "team_a": { /* current server stats */ },
    "team_b": { /* current server stats */ }
  },
  "server_timestamp": "2026-01-02T17:32:00.123456"
}
```

#### Client-Sent Messages

##### Update Stats

Client can send stat updates with timestamp for conflict resolution.

```json
{
  "type": "stats_update",
  "match_id": 123,
  "stats": {
    "match_id": 123,
    "team_a": {
      "id": 1,
      "team_stats": {
        "offence_yards": 255
      }
    },
    "team_b": { /* unchanged */ }
  },
  "timestamp": "2026-01-02T17:33:00.123456"
}
```

**Conflict Resolution:**
- Server compares client `timestamp` with last write timestamp
- If client timestamp is newer → update accepted and broadcast to all other clients
- If server timestamp is newer → update rejected, client receives `stats_sync` with current data

#### Stats Schema Details

##### Team Stats

```typescript
interface TeamStats {
  id: number;
  offence_yards: number;        // Total yards gained by offense
  pass_att: number;             // Total pass attempts
  run_att: number;              // Total run attempts
  avg_yards_per_att: number;    // Average yards per play (offence_yards / (pass_att + run_att))
  pass_yards: number;           // Total passing yards
  run_yards: number;            // Total rushing yards
  lost_yards: number;           // Total yards lost (sacks, fumbles, etc.)
  flag_yards: number;           // Total penalty yards (negative value)
  third_down_attempts: number;   // Third down attempts
  third_down_conversions: number; // Third down conversions
  fourth_down_attempts: number;   // Fourth down attempts
  fourth_down_conversions: number; // Fourth down conversions
  first_down_gained: number;     // First downs gained
  turnovers: number;             // Total turnovers (interceptions + lost fumbles)
}
```

##### Offense Stats

Keyed by `player_match_id` (player in match ID).

```typescript
interface OffenseStats {
  [playerMatchId: number]: {
    id: number;              // player_match_id
    pass_attempts: number;   // Pass attempts
    pass_received: number;   // Pass receptions
    pass_yards: number;      // Passing yards
    pass_td: number;         // Passing touchdowns
    run_attempts: number;    // Run attempts
    run_yards: number;      // Rushing yards
    run_avr: number;        // Average yards per rush
    run_td: number;         // Rushing touchdowns
    fumble: number;          // Fumbles
  };
}
```

##### QB Stats

Keyed by `player_match_id`.

```typescript
interface QBStats {
  [playerMatchId: number]: {
    id: number;              // player_match_id
    passes: number;          // Total passes attempted
    passes_completed: number; // Completed passes
    pass_yards: number;      // Passing yards
    pass_td: number;         // Passing touchdowns
    pass_avr: number;        // Pass completion percentage
    run_attempts: number;    // QB run attempts
    run_yards: number;      // QB rushing yards
    run_td: number;         // QB rushing touchdowns
    run_avr: number;        // QB average yards per rush
    fumble: number;          // QB fumbles
    interception: number;     // Interceptions thrown
    qb_rating: number;       // NFL-style QB rating
  };
}
```

**QB Rating Formula:**
```
QB Rating = (8.4 * pass_yards + 330 * pass_td + 100 * passes_completed - 200 * interception) / passes
```

##### Defense Stats

Keyed by `player_match_id`.

```typescript
interface DefenseStats {
  [playerMatchId: number]: {
    id: number;               // player_match_id
    tackles: number;          // Solo tackles
    assist_tackles: number;   // Assisted tackles
    sacks: number;            // Sacks
    interceptions: number;      // Interceptions
    fumble_recoveries: number; // Fumble recoveries
    flags: number;            // Penalties
  };
}
```

---

## WebSocket Message Formats

### General Message Structure

All WebSocket messages follow this structure:

```typescript
interface WebSocketMessage {
  type: string;           // Message type identifier
  match_id: number;       // Match ID
  [key: string]: any;     // Additional type-specific fields
  server_timestamp?: string; // ISO 8601 timestamp (server-sent only)
  timestamp?: string;      // ISO 8601 timestamp (client-sent only)
}
```

### Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `full_stats_update` | Server → Client | Complete match statistics sent on connection |
| `stats_update` | Server → Client | Incremental stats update (broadcast) |
| `stats_update` | Client → Server | Stats update request with conflict resolution |
| `stats_sync` | Server → Client | Server rejects client update, sends current stats |

### Connection Lifecycle

```
Client                              Server
  |                                   |
  |----- CONNECT ---------------------->|
  |                                   |
  |<---- full_stats_update ------------|
  |                                   |
  |----- stats_update (optional) ---->|
  |<---- stats_sync (if conflict) -----|
  |                                   |
  |<---- stats_update (broadcast) -----|
  |                                   |
  |----- stats_update --------------->|
  |                                   |
  |<---- stats_update (broadcast) -----|
  |                                   |
  |----- DISCONNECT ------------------->|
  |                                   |
  ```

### HTTP Endpoint: Match Statistics

#### GET /api/matches/id/{match_id}/stats/

Get complete match statistics for both teams without requiring a WebSocket connection.

**Endpoint:**
```
GET /api/matches/id/{match_id}/stats/
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID |

**Response (200 OK):**

```json
{
  "match_id": 123,
  "team_a": {
    "id": 1,
    "team_stats": {
      "id": 1,
      "offence_yards": 250,
      "pass_att": 20,
      "run_att": 30,
      "avg_yards_per_att": 5.0,
      "pass_yards": 150,
      "run_yards": 100,
      "lost_yards": 10,
      "flag_yards": -15,
      "third_down_attempts": 8,
      "third_down_conversions": 3,
      "fourth_down_attempts": 2,
      "fourth_down_conversions": 1,
      "first_down_gained": 15,
      "turnovers": 2
    },
    "offense_stats": {
      "456": {
        "id": 456,
        "pass_attempts": 10,
        "pass_received": 8,
        "pass_yards": 120,
        "pass_td": 1,
        "run_attempts": 5,
        "run_yards": 40,
        "run_avr": 8.0,
        "run_td": 0,
        "fumble": 0
      }
    },
    "qb_stats": {
      "789": {
        "id": 789,
        "passes": 15,
        "passes_completed": 10,
        "pass_yards": 150,
        "pass_td": 2,
        "pass_avr": 66.67,
        "run_attempts": 2,
        "run_yards": 10,
        "run_td": 0,
        "run_avr": 5.0,
        "fumble": 0,
        "interception": 1,
        "qb_rating": 85.5
      }
    },
    "defense_stats": {
      "101": {
        "id": 101,
        "tackles": 5,
        "assist_tackles": 3,
        "sacks": 1,
        "interceptions": 1,
        "fumble_recoveries": 1,
        "flags": 0
      }
    }
  },
  "team_b": {
    "id": 2,
    "team_stats": { /* same structure as team_a */ },
    "offense_stats": { /* same structure as team_a */ },
    "qb_stats": { /* same structure as team_a */ },
    "defense_stats": { /* same structure as team_a */ }
  }
}
```

**Error Responses:**

- **404 Not Found** - Match doesn't exist
- **500 Internal Server Error** - Server error

---

## Player Match API

### GET /api/matches/id/{match_id}/players_fulldata/

Get all players in a match with full related data (team, person, position) in a single optimized query.

**Endpoint:**
```
GET /api/matches/id/{match_id}/players_fulldata/
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID |

**Response (200 OK):**

```json
{
  "players": [
    {
      "id": 456,
      "player_id": 789,
      "player": {
        "id": 789,
        "player_eesl_id": 12345,
        "person_id": 123
      },
      "team": {
        "id": 1,
        "title": "Team A",
        "team_color": "#FF0000",
        "logo_url": "/static/uploads/teams/logos/1.jpg"
      },
      "position": {
        "id": 10,
        "title": "Quarterback",
        "category": "offense",
        "sport_id": 1
      },
      "player_team_tournament": {
        "id": 789,
        "player_team_tournament_eesl_id": 12345,
        "player_id": 789,
        "team_id": 1,
        "tournament_id": 5,
        "position_id": 10,
        "player_number": 12
      },
      "person": {
        "id": 123,
        "first_name": "John",
        "second_name": "Doe",
        "person_photo_url": "/static/uploads/persons/photos/123.jpg",
        "person_photo_icon_url": "/static/uploads/persons/icons/123.jpg",
        "person_photo_web_url": "/static/uploads/persons/web/123.jpg"
      },
      "is_starting": true,
      "starting_type": "offense"
    },
    {
      "id": 457,
      "player_id": 790,
      "player": { /* ... */ },
      "team": { /* ... */ },
      "position": {
        "id": 11,
        "title": "Linebacker",
        "category": "defense",
        "sport_id": 1
      },
      "player_team_tournament": { /* ... */ },
      "person": { /* ... */ },
      "is_starting": false,
      "starting_type": null
    }
  ]
}
```

**Response Schema:**

```typescript
interface PlayerMatchFullData {
  players: PlayerMatchDetail[];
}

interface PlayerMatchDetail {
  id: number;
  player_id: number | null;
  player: {
    id: number;
    player_eesl_id: number | null;
    person_id: number;
  } | null;
  team: {
    id: number;
    title: string;
    team_color: string;
    logo_url: string | null;
  } | null;
  position: {
    id: number;
    title: string;
    category: 'offense' | 'defense' | 'special' | 'other' | null;
    sport_id: number;
  } | null;
  player_team_tournament: {
    id: number;
    player_team_tournament_eesl_id: number | null;
    player_id: number;
    team_id: number;
    tournament_id: number;
    position_id: number | null;
    player_number: string;
  } | null;
  person: {
    id: number;
    first_name: string;
    second_name: string;
    person_photo_url: string | null;
    person_photo_icon_url: string | null;
    person_photo_web_url: string | null;
  } | null;
  is_starting: boolean | null;
  starting_type: 'offense' | 'defense' | 'special' | null;
}
```

**New Fields:**

| Field | Type | Description | Values |
| -- | -- | -- | -- |
| `position.category` | string | Position category (offense/defense/special/other) | 'offense', 'defense', 'special', 'other' |
| `is_starting` | boolean | Whether player is in starting lineup | true, false |
| `starting_type` | string | Starting lineup type | 'offense', 'defense', 'special', null |

**Response Schema:**

```typescript
interface PlayerMatchFullData {
  players: PlayerMatchDetail[];
}

interface PlayerMatchDetail {
  match_player: {
    id: number;
    player_match_eesl_id: number | null;
    player_team_tournament_id: number | null;
    match_position_id: number | null;
    match_id: number;
    match_number: string;
    team_id: number;
    is_start: boolean;
  };
  player_team_tournament: {
    id: number;
    player_team_tournament_eesl_id: number | null;
    player_id: number;
    team_id: number;
    tournament_id: number;
    position_id: number;
    player_number: string;
  };
  person: {
    id: number;
    first_name: string;
    second_name: string;
    person_photo_url: string | null;
    person_photo_icon_url: string | null;
    person_photo_web_url: string | null;
  } | null;
  position: {
    id: number;
    title: string;
    sport_id: number;
  } | null;
}
```

**Error Responses:**

- **404 Not Found** - Match doesn't exist
- **500 Internal Server Error** - Server error

---

## Team Rosters API

### GET /api/matches/id/{match_id}/team-rosters/

Get all team rosters (home, away, available) for a match in a single optimized response. This endpoint eliminates the need for multiple frontend API calls.

**Endpoint:**
```
GET /api/matches/id/{match_id}/team-rosters/
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|----------|-------------|
| `include_available` | boolean | true | Include available players (not in match) |
| `include_match_players` | boolean | true | Include players already in match |

**Response (200 OK):**

```json
{
  "match_id": 123,
  "home_roster": [
    {
      "id": 456,
      "player_id": 789,
      "player": {
        "id": 789,
        "player_eesl_id": 12345,
        "person_id": 123,
        "person": {
          "id": 123,
          "first_name": "Tom",
          "second_name": "Brady",
          "person_photo_url": "/static/uploads/persons/123.jpg"
        }
      },
      "team": {
        "id": 1,
        "title": "Team A",
        "team_color": "#FF0000",
        "logo_url": "/static/uploads/teams/logos/1.jpg"
      },
      "tournament": {
        "id": 5,
        "name": "Tournament 2026"
      },
      "player_number": "12",
      "is_home_team": true,
      "is_starting": true,
      "starting_type": "offense"
    }
  ],
  "away_roster": [
    {
      "id": 457,
      "player_id": 790,
      "player": {
        "id": 790,
        "player_eesl_id": 12346,
        "person_id": 124,
        "person": {
          "id": 124,
          "first_name": "Patrick",
          "second_name": "Mahomes",
          "person_photo_url": "/static/uploads/persons/124.jpg"
        }
      },
      "team": {
        "id": 2,
        "title": "Team B",
        "team_color": "#0000FF",
        "logo_url": "/static/uploads/teams/logos/2.jpg"
      },
      "tournament": {
        "id": 5,
        "name": "Tournament 2026"
      },
      "player_number": "15",
      "is_home_team": false,
      "is_starting": true,
      "starting_type": "offense"
    }
  ],
  "available_home": [
    {
      "id": 789,
      "player_id": 791,
      "player": {
        "id": 791,
        "player_eesl_id": 12347,
        "person_id": 125,
        "person": {
          "id": 125,
          "first_name": "Backup",
          "second_name": "Quarterback"
        }
      },
      "team": {
        "id": 1,
        "title": "Team A",
        "logo_url": "/static/uploads/teams/logos/1.jpg"
      },
      "tournament": {
        "id": 5,
        "name": "Tournament 2026"
      },
      "player_number": "8"
    }
  ],
  "available_away": [
    {
      "id": 790,
      "player_id": 792,
      "player": {
        "id": 792,
        "player_eesl_id": 12348,
        "person_id": 126,
        "person": {
          "id": 126,
          "first_name": "Backup",
          "second_name": "Running Back"
        }
      },
      "team": {
        "id": 2,
        "title": "Team B",
        "logo_url": "/static/uploads/teams/logos/2.jpg"
      },
      "tournament": {
        "id": 5,
        "name": "Tournament 2026"
      },
      "player_number": "22"
    }
  ]
}
```

**Error Responses:**

- **404 Not Found** - Match doesn't exist
- **500 Internal Server Error** - Server error

---

## Football Events API

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

Use this endpoint when displaying football plays in the scoreboard or play-by-play view where player information (name, photo, position, team) is needed for each event.

**Error Responses:**

- **404 Not Found** - Match doesn't exist
- **500 Internal Server Error** - Server error

---

## Error Responses

All API endpoints return consistent error responses.

### Standard Error Structure

```typescript
interface ErrorResponse {
  detail: string;
  [key: string]: any;
}
```

### HTTP Status Codes

| Status Code | Description | Example Scenarios |
|-------------|-------------|-------------------|
| 200 | Success | Request successful |
| 400 | Bad Request | Validation error, invalid data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Duplicate resource, creation failed |
| 422 | Unprocessable Entity | Business logic violation |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | External service failure |

### Example Error Responses

```json
{
  "detail": "Match 123 not found"
}
```

```json
{
  "detail": "Validation error: match_number must be at most 10 characters"
}
```

```json
{
  "detail": "Conflict - player match creation failed"
}
 ```

### GET /api/matches/id/{match_id}/full-context/

Get all data needed for match initialization: match, teams, sport with positions, tournament, players (home roster, away roster, available home, available away).

**Endpoint:**
```
GET /api/matches/id/{match_id}/full-context/
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID |

**Response (200 OK):**

```json
{
  "match": {
    "id": 123,
    "match_eesl_id": 100,
    "team_a_id": 1,
    "team_b_id": 2,
    "tournament_id": 5,
    "sport_id": 1,
    "match_date": "2025-01-03T10:00:00",
    "week": 1
  },
  "teams": {
    "home": {
      "id": 1,
      "title": "Team A",
      "team_logo_url": "https://...",
      "team_color": "#ff0000"
    },
    "away": {
      "id": 2,
      "title": "Team B",
      "team_logo_url": "https://...",
      "team_color": "#0000ff"
    }
  },
  "sport": {
    "id": 1,
    "title": "American Football",
    "description": "Football rules...",
    "positions": [
      {
        "id": 1,
        "title": "Quarterback",
        "sport_id": 1
      },
      {
        "id": 2,
        "title": "Linebacker",
        "sport_id": 1
      }
    ]
  },
  "tournament": {
    "id": 5,
    "title": "Tournament 2026",
    "sport_id": 1,
    "season_id": 1
  },
  "players": {
    "home_roster": [
      {
        "id": 456,
        "player_id": 789,
        "match_player": {
          "id": 456,
          "match_number": "10",
          "team_id": 1,
          "match_position_id": 1
        },
        "player_team_tournament": {
          "id": 789,
          "player_id": 789,
          "team_id": 1,
          "tournament_id": 5,
          "position_id": 1
        },
        "player": {
          "id": 789,
          "person_id": 456,
          "sport_id": 1
        },
        "person": {
          "id": 456,
          "first_name": "John",
          "second_name": "Doe",
          "person_photo_url": "https://..."
        },
        "position": {
          "id": 1,
          "title": "Quarterback",
          "sport_id": 1
        },
        "team": {
          "id": 1,
          "title": "Team A"
        }
      }
    ],
    "away_roster": [],
    "available_home": [],
    "available_away": [
      {
        "id": 790,
        "player_id": 790,
        "player_team_tournament": {
          "id": 790,
          "player_id": 790,
          "team_id": 2,
          "tournament_id": 5,
          "position_id": 2
        },
        "person": {
          "id": 457,
          "first_name": "Jane",
          "second_name": "Smith",
          "person_photo_url": "https://..."
        },
        "position": {
          "id": 2,
          "title": "Linebacker",
          "sport_id": 1
        },
        "team": {
          "id": 2,
          "title": "Team B"
        }
      }
    ]
  }
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Match not found |
| 500 | Internal server error |

---

## Integration Examples

### Example 1: Connect to Match Stats WebSocket

```typescript
async function connectToMatchStats(matchId: number) {
  const ws = new WebSocket(`ws://localhost:9000/api/matches/ws/matches/${matchId}/stats`);

  ws.onopen = () => {
    console.log('Connected to match stats WebSocket');
  };

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    switch (message.type) {
      case 'full_stats_update':
        console.log('Initial stats received:', message.stats);
        // Update UI with initial stats
        break;

      case 'stats_update':
        console.log('Stats updated:', message.stats);
        // Update UI with new stats
        break;

      case 'stats_sync':
        console.log('Sync required:', message.stats);
        // Update UI with server's current stats (client update rejected)
        break;

      default:
        console.warn('Unknown message type:', message.type);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = () => {
    console.log('WebSocket connection closed');
  };

  return ws;
}

// Usage
const matchId = 123;
const wsConnection = connectToMatchStats(matchId);
```

### Example 2: Update Stats via WebSocket

```typescript
function updateStats(ws: WebSocket, matchId: number, newStats: any) {
  const message = {
    type: 'stats_update',
    match_id: matchId,
    stats: newStats,
    timestamp: new Date().toISOString()
  };

  ws.send(JSON.stringify(message));
}

// Usage
updateStats(wsConnection, 123, {
  match_id: 123,
  team_a: {
    id: 1,
    team_stats: {
      offence_yards: 260,
      pass_att: 21
    }
  },
  team_b: { /* unchanged */ }
});
```

### Example 3: Fetch Players with Full Data

```typescript
async function fetchMatchPlayers(matchId: number) {
  try {
    const response = await fetch(
      `http://localhost:9000/api/matches/id/${matchId}/players_fulldata/`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Players fetched:', data.players);

    return data.players;
  } catch (error) {
    console.error('Failed to fetch players:', error);
    throw error;
  }
}

// Usage
fetchMatchPlayers(123)
  .then(players => {
    // Process players data
    players.forEach(player => {
      console.log(`${player.person?.first_name} ${player.person?.second_name} - ${player.position?.title}`);
    });
  })
  .catch(error => {
    // Handle error
  });
```

### Example 4: Display Team Stats

```typescript
interface TeamStatsDisplay {
  teamName: string;
  totalYards: number;
  passYards: number;
  runYards: number;
  avgYardsPerAtt: number;
  thirdDownEff: string;
  fourthDownEff: string;
  turnovers: number;
}

function formatTeamStats(teamStats: any): TeamStatsDisplay {
  const thirdDownPct = teamStats.third_down_attempts > 0
    ? ((teamStats.third_down_conversions / teamStats.third_down_attempts) * 100).toFixed(1)
    : '0.0';

  const fourthDownPct = teamStats.fourth_down_attempts > 0
    ? ((teamStats.fourth_down_conversions / teamStats.fourth_down_attempts) * 100).toFixed(1)
    : '0.0';

  return {
    teamName: `Team ${teamStats.id}`,
    totalYards: teamStats.offence_yards,
    passYards: teamStats.pass_yards,
    runYards: teamStats.run_yards,
    avgYardsPerAtt: teamStats.avg_yards_per_att,
    thirdDownEff: `${thirdDownPct}%`,
    fourthDownEff: `${fourthDownPct}%`,
    turnovers: teamStats.turnovers
  };
}

// Usage in component
function renderTeamStats(teamStats: any) {
  const stats = formatTeamStats(teamStats);

  return `
    <div class="team-stats">
      <h3>${stats.teamName}</h3>
      <div class="stat-row">
        <span>Total Yards:</span>
        <span>${stats.totalYards}</span>
      </div>
      <div class="stat-row">
        <span>Pass Yards:</span>
        <span>${stats.passYards}</span>
      </div>
      <div class="stat-row">
        <span>Run Yards:</span>
        <span>${stats.runYards}</span>
      </div>
      <div class="stat-row">
        <span>Avg/Att:</span>
        <span>${stats.avgYardsPerAtt}</span>
      </div>
      <div class="stat-row">
        <span>3rd Down:</span>
        <span>${stats.thirdDownEff}</span>
      </div>
      <div class="stat-row">
        <span>4th Down:</span>
        <span>${stats.fourthDownEff}</span>
      </div>
      <div class="stat-row">
        <span>Turnovers:</span>
        <span>${stats.turnovers}</span>
      </div>
    </div>
  `;
}
```

### Example 5: React Hook for Match Stats

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';

interface MatchStats {
  match_id: number;
  team_a: {
    id: number;
    team_stats: any;
    offense_stats: any;
    qb_stats: any;
    defense_stats: any;
  };
  team_b: {
    id: number;
    team_stats: any;
    offense_stats: any;
    qb_stats: any;
    defense_stats: any;
  };
}

export function useMatchStats(matchId: number) {
  const [stats, setStats] = useState<MatchStats | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Update stats via WebSocket
  const updateStats = useCallback((newStats: Partial<MatchStats>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'stats_update',
        match_id: matchId,
        stats: newStats,
        timestamp: new Date().toISOString()
      }));
    }
  }, [matchId]);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:9000/api/matches/ws/matches/${matchId}/stats`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'full_stats_update':
        case 'stats_update':
          setStats(message.stats);
          break;

        case 'stats_sync':
          setStats(message.stats);
          console.warn('Stats sync: server rejected client update');
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    ws.onclose = () => {
      setConnected(false);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [matchId]);

  return { stats, connected, updateStats };
}

// Usage
function MatchStatsComponent({ matchId }: { matchId: number }) {
  const { stats, connected, updateStats } = useMatchStats(matchId);

  if (!stats) {
    return <div>Loading stats...</div>;
  }

  return (
    <div>
      <div className="connection-status">
        Status: {connected ? 'Connected' : 'Disconnected'}
      </div>
      <div className="team-a-stats">
        <h3>Team A</h3>
        <p>Total Yards: {stats.team_a.team_stats.offence_yards}</p>
        <p>Turnovers: {stats.team_a.team_stats.turnovers}</p>
      </div>
      <div className="team-b-stats">
        <h3>Team B</h3>
        <p>Total Yards: {stats.team_b.team_stats.offence_yards}</p>
        <p>Turnovers: {stats.team_b.team_stats.turnovers}</p>
      </div>
      <button
        onClick={() => updateStats({
          match_id: matchId,
          team_a: {
            id: stats.team_a.id,
            team_stats: {
              ...stats.team_a.team_stats,
              offence_yards: stats.team_a.team_stats.offence_yards + 1
            }
          },
          team_b: stats.team_b
        })}
        disabled={!connected}
      >
        Increment Team A Yards
      </button>
    </div>
  );
}
```

---

## Notes

### WebSocket Connection Stability

- WebSocket connections may drop due to network issues
- Implement reconnection logic with exponential backoff
- Handle connection states gracefully in UI

### Timestamps

- All timestamps are in ISO 8601 format: `YYYY-MM-DDTHH:mm:ss.ssssss`
- Client timestamps should be in UTC
- Server timestamps are always UTC

### Conflict Resolution

- Client updates with older timestamps are rejected
- Server always wins in conflict scenarios
- Clients receive `stats_sync` messages with current data after conflicts
- Implement UI indicators when updates are rejected

### Performance

- Players endpoint uses single optimized query with `selectinload` for performance
- Stats are cached server-side (invalidated on updates)
- WebSocket connections are pooled per match

### Future Enhancements

- **Authentication**: WebSocket authentication support (planned)
- **Historical Stats**: Historical match statistics (planned)

---

## Support

For issues or questions regarding these APIs, please contact the backend team or create an issue in the repository.
