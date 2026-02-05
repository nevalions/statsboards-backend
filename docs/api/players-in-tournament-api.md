# Players in Tournament API

### GET /api/tournaments/id/{tournament_id}/players/

Get all players participating in a specific tournament, sorted by name (second_name, first_name).

**Endpoint:**
```
GET /api/tournaments/id/{tournament_id}/players/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tournament_id` | integer | Yes | Tournament ID |

**Response (200 OK):**

```json
[
  {
    "id": 10,
    "player_team_tournament_eesl_id": 12345,
    "player_id": 789,
    "team_id": 5,
    "position_id": 3,
    "tournament_id": 2,
    "player_number": "12",
    "player": {
      "id": 789,
      "sport_id": 1,
      "person_id": 123,
      "player_eesl_id": 98765,
      "person": {
        "id": 123,
        "person_eesl_id": null,
        "first_name": "John",
        "second_name": "Doe",
        "person_photo_url": "/static/uploads/persons/photos/123.jpg",
        "person_photo_icon_url": "/static/uploads/persons/icons/123.jpg",
        "person_photo_web_url": "/static/uploads/persons/web/123.jpg",
        "person_dob": "1990-01-15T00:00:00"
      }
    },
    "team": {
      "id": 5,
      "team_eesl_id": 1001,
      "title": "Team Alpha",
      "city": "Boston",
      "description": "Professional sports team",
      "team_logo_url": "/static/uploads/teams/logos/5.jpg",
      "team_logo_icon_url": "/static/uploads/teams/icons/5.jpg",
      "team_logo_web_url": "/static/uploads/teams/web/5.jpg",
      "team_color": "#FF0000",
      "sport_id": 1
    },
    "position": {
      "id": 3,
      "title": "Quarterback",
      "category": "offense",
      "sport_id": 1
    }
  },
  {
    "id": 11,
    "player_team_tournament_eesl_id": 12346,
    "player_id": 790,
    "team_id": 5,
    "position_id": 4,
    "tournament_id": 2,
    "player_number": "15",
    "player": {
      "id": 790,
      "sport_id": 1,
      "person_id": 124,
      "player_eesl_id": 98766,
      "person": {
        "id": 124,
        "person_eesl_id": null,
        "first_name": "Alice",
        "second_name": "Anderson",
        "person_photo_url": "/static/uploads/persons/photos/124.jpg",
        "person_photo_icon_url": "/static/uploads/persons/icons/124.jpg",
        "person_photo_web_url": "/static/uploads/persons/web/124.jpg",
        "person_dob": "1992-03-22T00:00:00"
      }
    },
    "team": {
      "id": 5,
      "team_eesl_id": 1001,
      "title": "Team Alpha",
      "city": "Boston",
      "description": "Professional sports team",
      "team_logo_url": "/static/uploads/teams/logos/5.jpg",
      "team_logo_icon_url": "/static/uploads/teams/icons/5.jpg",
      "team_logo_web_url": "/static/uploads/teams/web/5.jpg",
      "team_color": "#FF0000",
      "sport_id": 1
    },
    "position": {
      "id": 4,
      "title": "Wide Receiver",
      "category": "offense",
      "sport_id": 1
    }
  }
]
```

**Response Schema:**

```typescript
interface PlayerTeamTournamentWithFullDetails {
  id: number;
  player_team_tournament_eesl_id: number | null;
  player_id: number | null;
  team_id: number | null;
  position_id: number | null;
  tournament_id: number | null;
  player_number: string;
  player: PlayerWithPerson;
  team: Team | null;
  position: Position | null;
}

interface PlayerWithPerson {
  id: number;
  sport_id: number | null;
  person_id: number | null;
  player_eesl_id: number | null;
  person: Person;
}

interface Person {
  id: number;
  person_eesl_id: number | null;
  first_name: string;
  second_name: string;
  person_photo_url: string | null;
  person_photo_icon_url: string | null;
  person_photo_web_url: string | null;
  person_dob: string | null;
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
  sport_id: number;
}

interface Position {
  id: number;
  title: string;
  category: 'offense' | 'defense' | 'special' | 'other' | null;
  sport_id: number;
}
```

**Behavior:**

- Returns all `PlayerTeamTournament` records for the specified tournament
- Results are sorted by player name (second_name, then first_name) in ascending alphabetical order
- Returns empty array if tournament doesn't exist or has no players
- No pagination - returns all players in a single response
- All related data (player, person, team, position) is pre-loaded

**Use Cases:**

- **Tournament roster display**: Show all players in a tournament
- **Roster management**: View and manage all tournament participants
- **Team rosters**: See which players are on which teams within a tournament

**Examples:**

1. **Get all players in tournament:**
```
GET /api/tournaments/id/2/players/
```

2. **Use to display tournament roster:**
```typescript
async function loadTournamentPlayers(tournamentId: number) {
  const response = await fetch(
    `/api/tournaments/id/${tournamentId}/players/`
  );
  const players: PlayerTeamTournamentWithFullDetails[] = await response.json();
  
  // Display roster
  return players.map(ptt => ({
    id: ptt.id,
    name: `${ptt.player.person.first_name} ${ptt.player.person.second_name}`,
    team: ptt.team?.title || 'Unassigned',
    position: ptt.position?.title,
    number: ptt.player_number,
    avatar: ptt.player.person.person_photo_icon_url
  }));
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - players returned (empty array if none) |
| 500 | Internal Server Error - server error |

**Note:** Returns empty array (200 OK) if tournament doesn't exist, making it safe for use without requiring error handling.

---

### GET /api/tournaments/id/{tournament_id}/players/paginated

Get all players participating in a specific tournament with pagination and search functionality. Results are sorted by name (second_name by default) and include player details.

**Endpoint:**
```
GET /api/tournaments/id/{tournament_id}/players/paginated
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
  player_number: string | null;
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
- Pattern matching: `%query%` (matches anywhere in name)
- Empty `search` parameter returns all players in tournament
- Default sorting: by `second_name` (ascending), then by `id` (ascending) when no custom order is specified

**Use Cases:**

- **Paginated tournament roster**: Display players in pages for large tournaments
- **Search by player name**: Quickly find specific players in a tournament
- **Custom ordering**: Sort players by different criteria as needed
- **Performance**: Use pagination instead of loading all players at once

**Examples:**

1. **Get first page of players in tournament:**
```
GET /api/tournaments/id/2/players/paginated?page=1&items_per_page=20
```

2. **Search players by name with pagination:**
```
GET /api/tournaments/id/2/players/paginated?search=Smith&page=1&items_per_page=20
```

3. **Get second page with custom ordering:**
```
GET /api/tournaments/id/2/players/paginated?page=2&items_per_page=10&order_by=second_name&order_by_two=id&ascending=false
```

4. **Implement search with pagination in frontend:**
```typescript
async function loadTournamentPlayersPaginated(
  tournamentId: number,
  page: number = 1,
  searchQuery: string = ''
) {
  const params = new URLSearchParams({
    page: page.toString(),
    items_per_page: '20'
  });

  if (searchQuery) {
    params.append('search', searchQuery);
  }

  const response = await fetch(
    `/api/tournaments/id/${tournamentId}/players/paginated?${params}`
  );
  const result: PaginatedPlayerWithDetailsResponse = await response.json();

  return {
    players: result.data,
    pagination: result.metadata
  };
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - players returned (empty array if none) |
| 400 | Bad Request - invalid query parameters |
| 404 | Not Found - tournament_id doesn't exist |
| 500 | Internal Server Error - server error |

---
