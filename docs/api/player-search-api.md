# Player Search API

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
