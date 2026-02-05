# Teams in Tournament API

### GET /api/tournaments/id/{tournament_id}/teams/

Retrieves all teams participating in a specific tournament, sorted alphabetically by team title.

**Endpoint:**
```
GET /api/tournaments/id/{tournament_id}/teams/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tournament_id` | integer | Yes | Tournament ID |

**Response (200 OK):**

```json
[
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
  },
  {
    "id": 2,
    "team_eesl_id": 12346,
    "title": "Liverpool",
    "city": "Liverpool",
    "description": "Premier League football club",
    "team_logo_url": "https://example.com/logos/liverpool.png",
    "team_logo_icon_url": "https://example.com/icons/liverpool-icon.png",
    "team_logo_web_url": "https://example.com/web/liverpool.png",
    "team_color": "#C8102E",
    "sponsor_line_id": null,
    "main_sponsor_id": null,
    "sport_id": 1
  }
]
```

**Behavior:**

- Returns all teams associated with the tournament via `team_tournament` table
- Results are sorted alphabetically by team title (ascending order)
- Returns empty array if tournament doesn't exist or has no teams

**Examples:**

1. **Get all teams in tournament:**
```
GET /api/tournaments/id/1/teams/
```

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

### GET /api/team_in_tournament/tournament/id/{tournament_id}/teams

Retrieves all teams participating in a specific tournament, sorted alphabetically by team title.

**Endpoint:**
```
GET /api/team_in_tournament/tournament/id/{tournament_id}/teams
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tournament_id` | integer | Yes | Tournament ID |

**Response (200 OK):**

```json
[
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
  },
  {
    "id": 2,
    "team_eesl_id": 12346,
    "title": "Liverpool",
    "city": "Liverpool",
    "description": "Premier League football club",
    "team_logo_url": "https://example.com/logos/liverpool.png",
    "team_logo_icon_url": "https://example.com/icons/liverpool-icon.png",
    "team_logo_web_url": "https://example.com/web/liverpool.png",
    "team_color": "#C8102E",
    "sponsor_line_id": null,
    "main_sponsor_id": null,
    "sport_id": 1
  }
]
```

**Behavior:**

- Returns all teams associated with the tournament via `team_tournament` table
- Results are sorted alphabetically by team title (ascending order)
- Returns empty array if tournament doesn't exist or has no teams

**Examples:**

1. **Get all teams in tournament:**
```
GET /api/team_in_tournament/tournament/id/1/teams
```

### POST /api/team_in_tournament/{team_id}in{tournament_id}

Create a new team-tournament association. This adds a team to a tournament.

**Endpoint:**
```
POST /api/team_in_tournament/{team_id}in{tournament_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `team_id` | integer | Yes | Team ID to add to tournament |
| `tournament_id` | integer | Yes | Tournament ID to add team to |

**Response (200 OK):**

```json
{
  "id": 1,
  "tournament_id": 5,
  "team_id": 10
}
```

**Response Schema:**

```typescript
interface TeamTournamentSchema {
  id: number;
  tournament_id: number;
  team_id: number;
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - relation created |
| 409 | Conflict - relation already exists for this team+tournament combination |
| 500 | Internal Server Error - server error |

**Behavior:**

- Creates a new association between a team and tournament
- Returns 409 if the team is already in the tournament (relation already exists)
- No request body - IDs are passed as path parameters

**Examples:**

1. **Add team 10 to tournament 5:**
```
POST /api/team_in_tournament/10in5
```

### GET /api/team_in_tournament/{team_id}in{tournament_id}

Get a specific team-tournament relation by team ID and tournament ID.

**Endpoint:**
```
GET /api/team_in_tournament/{team_id}in{tournament_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `team_id` | integer | Yes | Team ID |
| `tournament_id` | integer | Yes | Tournament ID |

**Response (200 OK):**

```json
{
  "id": 1,
  "tournament_id": 5,
  "team_id": 10
}
```

**Response Schema:**

```typescript
interface TeamTournamentSchema {
  id: number;
  tournament_id: number;
  team_id: number;
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - relation found |
| 404 | Not Found - team-tournament relation doesn't exist |
| 500 | Internal Server Error - server error |

**Behavior:**

- Returns the team-tournament association record
- Use this endpoint to verify if a team is in a tournament
- Returns 404 if the relation doesn't exist

**Examples:**

1. **Get relation for team 10 in tournament 5:**
```
GET /api/team_in_tournament/10in5
```

### PUT /api/team_in_tournament/{item_id}/

Update a team-tournament relation by its ID.

**Endpoint:**
```
PUT /api/team_in_tournament/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Team-Tournament relation ID |

**Request Body:**

```json
{
  "tournament_id": 5,
  "team_id": 10
}
```

**Request Schema:**

```typescript
interface TeamTournamentSchemaUpdate {
  tournament_id: number | null; // Optional - new tournament ID
  team_id: number | null; // Optional - new team ID
}
```

**Response (200 OK):**

```json
{
  "id": 1,
  "tournament_id": 5,
  "team_id": 10
}
```

**Response Schema:**

```typescript
interface TeamTournamentSchema {
  id: number;
  tournament_id: number;
  team_id: number;
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - relation updated |
| 404 | Not Found - team-tournament relation ID doesn't exist |
| 422 | Validation error - invalid request data |
| 500 | Internal Server Error - server error |

**Behavior:**

- Updates the team or tournament ID of an existing relation
- Only updates provided fields (partial update)
- Use this endpoint to move a team from one tournament to another

**Examples:**

1. **Update team in relation:**
```
PUT /api/team_in_tournament/1/

{
  "team_id": 15
}
```

2. **Update tournament in relation:**
```
PUT /api/team_in_tournament/1/

{
  "tournament_id": 8
}
```

### DELETE /api/team_in_tournament/{team_id}in{tournament_id}

Delete a team-tournament relation by team ID and tournament ID. This removes a team from a tournament.

**Endpoint:**
```
DELETE /api/team_in_tournament/{team_id}in{tournament_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `team_id` | integer | Yes | Team ID to remove from tournament |
| `tournament_id` | integer | Yes | Tournament ID to remove team from |

**Response (200 OK):**

No response body (204 No Content)

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - relation deleted |
| 500 | Internal Server Error - server error |

**Behavior:**

- Deletes the team-tournament association
- Team is no longer participating in the tournament
- Does not delete the team or tournament records, only the relation

**Examples:**

1. **Remove team 10 from tournament 5:**
```
DELETE /api/team_in_tournament/10in5
```

---
