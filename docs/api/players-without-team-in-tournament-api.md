# Players Without Team in Tournament API

### GET /api/tournaments/id/{tournament_id}/players/without-team

Get all players in a tournament who are not connected to any team (team_id is NULL). Useful for finding unassigned players in a tournament.

**Endpoint:**
```
GET /api/tournaments/id/{tournament_id}/players/without-team
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tournament_id` | integer | Yes | Tournament ID |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|----------|-------------|
| `search` | string | No | - | Search query for player first name or second name |
| `page` | integer | No | 1 | Page number (1-based) |
| `items_per_page` | integer | No | 20 | Items per page (max 100) |
| `order_by` | string | No | "second_name" | First sort column |
| `order_by_two` | string | No | "id" | Second sort column |
| `ascending` | boolean | No | true | Sort order (true=asc, false=desc) |

**Response (200 OK):**

```json
{
  "data": [
    {
      "id": 1,
      "player_team_tournament_eesl_id": null,
      "player_id": 789,
      "position_id": null,
      "team_id": null,
      "tournament_id": 5,
      "player_number": "12",
      "first_name": "John",
      "second_name": "Doe",
      "team_title": null,
      "position_title": null
    },
    {
      "id": 2,
      "player_team_tournament_eesl_id": null,
      "player_id": 790,
      "position_id": null,
      "team_id": null,
      "tournament_id": 5,
      "player_number": "15",
      "first_name": "Jane",
      "second_name": "Smith",
      "team_title": null,
      "position_title": null
    }
  ],
  "metadata": {
    "page": 1,
    "items_per_page": 20,
    "total_items": 2,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

**Response Schema:**

```typescript
interface PaginatedPlayerTeamTournamentWithDetailsResponse {
  data: PlayerTeamTournamentWithDetails[];
  metadata: PaginationMetadata;
}

interface PlayerTeamTournamentWithDetails {
  id: number;
  player_team_tournament_eesl_id: number | null;
  player_id: number | null;
  position_id: number | null;
  team_id: number | null;
  tournament_id: number | null;
  player_number: string;
  first_name: string | null;
  second_name: string | null;
  team_title: string | null;
  position_title: string | null;
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
- Pattern matching: `%query%` (matches anywhere in name)
- Only returns players with `team_id` = NULL (not assigned to any team)
- Empty `search` parameter returns all unassigned players in tournament
- Default sorting: by `second_name` (ascending), then by `id` (ascending) when no custom order is specified

**Use Cases:**

- **Finding unassigned players**: Discover players in tournament without a team assignment
- **Roster management**: Identify players who need to be assigned to a team
- **Team formation**: Browse available unassigned players for team creation

**Examples:**

1. **Get all players without team in tournament:**
```
GET /api/tournaments/id/5/players/without-team?page=1&items_per_page=20
```

2. **Search unassigned players by name:**
```
GET /api/tournaments/id/5/players/without-team?search=John&page=1&items_per_page=20
```

3. **Get second page with custom ordering:**
```
GET /api/tournaments/id/5/players/without-team?page=2&items_per_page=10&order_by=second_name&order_by_two=id&ascending=false
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - players returned (empty array if none) |
| 400 | Bad Request - invalid query parameters |
| 404 | Not Found - tournament_id doesn't exist |
| 500 | Internal Server Error - server error |

---

### GET /api/tournaments/id/{tournament_id}/players/without-team/all

Get all players in a tournament who are not connected to any team (team_id is NULL) without pagination. Results are sorted by name (second_name, then first_name). Useful for retrieving all unassigned players for dropdown lists or when pagination is not needed.

**Endpoint:**
```
GET /api/tournaments/id/{tournament_id}/players/without-team/all
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tournament_id` | integer | Yes | Tournament ID |

**Response (200 OK):**

```json
[
  {
    "id": 789,
    "sport_id": 1,
    "person_id": 123,
    "player_eesl_id": 98765,
    "first_name": "John",
    "second_name": "Doe",
    "player_team_tournaments": []
  },
  {
    "id": 790,
    "sport_id": 1,
    "person_id": 124,
    "player_eesl_id": 98766,
    "first_name": "Jane",
    "second_name": "Smith",
    "player_team_tournaments": []
  }
]
```

**Response Schema:**

```typescript
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
  player_number: string | null;
  team_id: number | null;
  team_title: string | null;
  position_id: number | null;
  position_title: string | null;
  tournament_id: number | null;
}
```

**Behavior:**

- Returns all players with `team_id` = NULL (not assigned to any team) for the specified tournament
- Results are sorted by `second_name` (ascending), then by `first_name` (ascending)
- No pagination - returns all unassigned players in a single response
- Returns empty array if tournament doesn't exist or has no unassigned players

**Use Cases:**

- **Dropdown selection**: Populate dropdown lists with all unassigned players
- **Team assignment UI**: Display all available players for assignment
- **Small tournaments**: When the number of unassigned players is manageable without pagination
- **Offline functionality**: Load all unassigned players once and filter client-side

**Examples:**

1. **Get all unassigned players in tournament:**
```
GET /api/tournaments/id/5/players/without-team/all
```

2. **Use in dropdown for player assignment:**
```typescript
async function loadUnassignedPlayers(tournamentId: number) {
  const response = await fetch(
    `/api/tournaments/id/${tournamentId}/players/without-team/all`
  );
  const players: PlayerWithDetails[] = await response.json();

  // Render dropdown
  return players.map(player => ({
    value: player.id,
    label: `${player.first_name} ${player.second_name}`,
    avatar: null
  }));
}
```

3. **Display unassigned players list:**
```typescript
async function displayUnassignedPlayers(tournamentId: number) {
  const response = await fetch(
    `/api/tournaments/id/${tournamentId}/players/without-team/all`
  );
  const players: PlayerWithDetails[] = await response.json();

  return players.map(player => ({
    id: player.id,
    name: `${player.first_name} ${player.second_name}`,
    sportId: player.sport_id
  }));
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - players returned (empty array if none) |
| 500 | Internal Server Error - server error |

**Note:** Returns empty array (200 OK) if tournament doesn't exist or has no unassigned players, making it safe for dropdown use cases without error handling.

**Comparison with Paginated Version:**

- Use `/players/without-team/all` when:
  - You need all unassigned players at once
  - The number of players is small/known
  - Building a dropdown or similar UI component

- Use `/players/without-team` (paginated) when:
  - You need search functionality
  - The number of players is large
  - Building a paginated data table with filters

---
