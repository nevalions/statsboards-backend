# Seasons API

The Seasons API provides comprehensive management of tournament seasons with two access patterns: the **Global Settings API** for basic CRUD operations and the **Direct Seasons API** for advanced queries and tournament/season relationships.

### API Selection Guide

| Use Case | Recommended API | Reason |
|----------|----------------|--------|
| Basic CRUD (Create, Read, Update, Delete) | Global Settings API `/api/settings/seasons/*` | Simple, consistent with other settings operations |
| Get all seasons ordered by year | Global Settings API `/api/settings/seasons/` | Direct, pre-sorted result |
| Query seasons by year, pagination, search | Direct Seasons API `/api/seasons/*` | Advanced filtering and search capabilities |
| Get tournaments/teams/matches by season year | Direct Seasons API `/api/seasons/year/{year}/*` | Specialized endpoints for related data |
| Admin operations (delete season) | Direct Seasons API `/api/seasons/id/{id}` | Enforces admin role requirement |

**Note:** The Global Settings API and Direct Seasons API share the same underlying database model and schemas. The choice depends on your specific use case and required functionality.

### Validation Rules

All seasons must adhere to the following validation rules:

| Field | Type | Constraints | Default |
|-------|------|-------------|---------|
| `year` | integer | 1900-2999, **must be unique** | Required |
| `description` | string | Optional text description | `""` |
| `iscurrent` | boolean | Only one season can be `true` at a time | `false` |

**Current Season Behavior:**
- When creating or updating a season with `iscurrent: true`, all other seasons are automatically set to `iscurrent: false`
- Only one season can be marked as current at any time
- This ensures consistency across the application for tournament organization

**Cascade Delete:**
- Deleting a season will cascade delete all associated tournaments
- This is a destructive operation that affects all dependent data

### Response Schemas

```typescript
interface SeasonSchema {
  id: number;
  year: number; // 1900-2999, unique
  description: string | null;
  iscurrent: boolean;
}

interface SeasonSchemaCreate {
  year: number; // 1900-2999, unique
  description: string | null; // Optional
  iscurrent: boolean; // Optional, defaults to false
}

interface SeasonSchemaUpdate {
  year: number | null; // Optional - 1900-2999
  description: string | null; // Optional
  iscurrent: boolean | null; // Optional
}

interface PaginatedSeasonResponse {
  data: SeasonSchema[];
  metadata: PaginationMetadata;
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

---

### Direct Seasons API Endpoints

The direct seasons API at `/api/seasons/*` provides 11 endpoints for advanced season management, including CRUD operations and specialized queries for tournaments, teams, and matches by season year.

#### GET /api/seasons/

Get all seasons (no pagination). Returns simple list of all seasons.

**Endpoint:**
```
GET /api/seasons/
```

**Response (200 OK):**
```json
[
  {
    "id": 2,
    "year": 2024,
    "description": "2024 Season",
    "iscurrent": true
  },
  {
    "id": 1,
    "year": 2023,
    "description": "2023 Season",
    "iscurrent": false
  }
]
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

#### GET /api/seasons/paginated

Search seasons by description with pagination, sorting, and filtering.

**Endpoint:**
```
GET /api/seasons/paginated
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (1-based) |
| `items_per_page` | integer | No | 20 | Items per page (max 100) |
| `order_by` | string | No | "year" | First sort column |
| `order_by_two` | string | No | "id" | Second sort column |
| `ascending` | boolean | No | true | Sort order (true=asc, false=desc) |
| `search` | string | No | - | Search query for description (case-insensitive) |

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 2,
      "year": 2024,
      "description": "2024 Season",
      "iscurrent": true
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

**Behavior:**
- Search is case-insensitive and uses partial matching on `description` field
- Uses ICU collation for consistent international character handling
- Defaults to ordering by `year` ascending, then by `id`

**Examples:**

1. **Search seasons by description:**
```
GET /api/seasons/paginated?search=2024&page=1&items_per_page=20
```

2. **Custom ordering:**
```
GET /api/seasons/paginated?order_by=iscurrent&order_by_two=year&ascending=false
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 422 | Validation error - invalid query parameters |
| 500 | Internal server error |

---

#### GET /api/seasons/id/{item_id}/

Get a season by ID.

**Endpoint:**
```
GET /api/seasons/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Season ID to retrieve |

**Response (200 OK):**
```json
{
  "id": 2,
  "year": 2024,
  "description": "2024 Season",
  "iscurrent": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Season not found |
| 500 | Internal server error |

---

#### GET /api/seasons/year/{season_year}

Get a season by year.

**Endpoint:**
```
GET /api/seasons/year/{season_year}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `season_year` | integer | Yes | Season year to retrieve |

**Response (200 OK):**
```json
{
  "id": 2,
  "year": 2024,
  "description": "2024 Season",
  "iscurrent": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Season with given year not found |
| 500 | Internal server error |

**Use Case:**
Use this endpoint when you need to find a season by its year rather than ID. This is common when filtering tournaments or matches by season year.

---

#### GET /api/seasons/id/{item_id}/sports/id/{sport_id}/tournaments

Get all tournaments for a specific season and sport combination, ordered by title.

**Endpoint:**
```
GET /api/seasons/id/{item_id}/sports/id/{sport_id}/tournaments
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Season ID |
| `sport_id` | integer | Yes | Sport ID |

**Response (200 OK):**
```json
[
  {
    "id": 5,
    "title": "Premier League 2024",
    "season_id": 2,
    "sport_id": 1
  },
  {
    "id": 6,
    "title": "FA Cup 2024",
    "season_id": 2,
    "sport_id": 1
  }
]
```

**Behavior:**
- Returns all tournaments belonging to the specified season and sport
- Results are ordered alphabetically by `title` in ascending order
- Returns empty array if no tournaments match the criteria

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

**Use Cases:**
- Display tournaments for a specific season/sport combination
- Populate tournament selectors in season/sport filtered views
- Query tournament data for analytics or reporting by season and sport

---

#### GET /api/seasons/year/{year}/tournaments

Get all tournaments for a specific season year, ordered by title.

**Endpoint:**
```
GET /api/seasons/year/{year}/tournaments
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `year` | integer | Yes | Season year |

**Response (200 OK):**
```json
[
  {
    "id": 5,
    "title": "Premier League 2024",
    "season_id": 2,
    "sport_id": 1
  },
  {
    "id": 7,
    "title": "La Liga 2024",
    "season_id": 2,
    "sport_id": 2
  }
]
```

**Behavior:**
- Returns all tournaments belonging to the specified season year
- Results are ordered alphabetically by `title` in ascending order
- Includes tournaments from all sports for that season
- Returns empty array if no tournaments exist for that year

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

**Use Cases:**
- Display all tournaments for a season across all sports
- Season-overview pages
- Tournament selection by season

---

#### GET /api/seasons/year/{year}/sports/id/{sport_id}/tournaments

Get all tournaments for a specific season year and sport combination, ordered by title.

**Endpoint:**
```
GET /api/seasons/year/{year}/sports/id/{sport_id}/tournaments
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `year` | integer | Yes | Season year |
| `sport_id` | integer | Yes | Sport ID |

**Response (200 OK):**
```json
[
  {
    "id": 5,
    "title": "Premier League 2024",
    "season_id": 2,
    "sport_id": 1
  }
]
```

**Behavior:**
- Returns all tournaments belonging to the specified season year and sport
- Results are ordered alphabetically by `title` in ascending order
- Returns empty array if no tournaments match the criteria

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

**Use Case:**
Alternative to `/api/seasons/id/{item_id}/sports/id/{sport_id}/tournaments` when you have the season year instead of the season ID. Useful when working with year-based filters rather than ID-based lookups.

---

#### GET /api/seasons/year/{year}/teams

Get all teams that participated in tournaments during a specific season year.

**Endpoint:**
```
GET /api/seasons/year/{year}/teams
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `year` | integer | Yes | Season year |

**Response (200 OK):**
```json
[
  {
    "id": 10,
    "title": "Manchester United",
    "sport_id": 1
  },
  {
    "id": 11,
    "title": "Chelsea FC",
    "sport_id": 1
  }
]
```

**Behavior:**
- Returns all unique teams that participated in any tournament during the specified season year
- Traverses two levels: Season → Tournaments → Teams
- Automatically deduplicates teams (same team may appear in multiple tournaments)
- Returns empty array if no teams participated in that season

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

**Use Cases:**
- Display all teams that were active in a season
- Season-overview team listings
- Team selection filters by season
- Historical team participation reporting

---

#### GET /api/seasons/year/{year}/matches

Get all matches that took place during tournaments in a specific season year.

**Endpoint:**
```
GET /api/seasons/year/{year}/matches
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `year` | integer | Yes | Season year |

**Response (200 OK):**
```json
[
  {
    "id": 100,
    "tournament_id": 5,
    "team_home_id": 10,
    "team_away_id": 11,
    "match_date": "2024-01-15T19:00:00Z",
    "score_home": 2,
    "score_away": 1
  }
]
```

**Behavior:**
- Returns all matches from all tournaments in the specified season year
- Traverses two levels: Season → Tournaments → Matches
- Results are unsorted (order depends on database)
- Returns empty array if no matches occurred in that season

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

**Use Cases:**
- Display all matches for a season
- Season-based match statistics
- Historical match data retrieval
- Season match archives

---

#### POST /api/seasons/

Create a new season.

**Endpoint:**
```
POST /api/seasons/
```

**Request Body:**
```json
{
  "year": 2025,
  "description": "2025 Season",
  "iscurrent": true
}
```

**Request Schema:**
```typescript
interface SeasonSchemaCreate {
  year: number; // 1900-2999, must be unique
  description: string | null; // Optional
  iscurrent: boolean; // Optional, defaults to false
}
```

**Response (200 OK):**
```json
{
  "id": 3,
  "year": 2025,
  "description": "2025 Season",
  "iscurrent": true
}
```

**Behavior:**
- If `iscurrent` is set to `true`, all other seasons are automatically set to `iscurrent: false`
- Returns 400 error if year is not unique
- Returns 422 error if year is outside range 1900-2999

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Error creating new season (e.g., duplicate year) |
| 422 | Validation error - year out of range (must be 1900-2999) |
| 500 | Internal server error |

**Example Usage:**
```bash
# Create a new season as current
POST /api/seasons/
{
  "year": 2025,
  "description": "2025 Season",
  "iscurrent": true
}

# Create a new season (not current)
POST /api/seasons/
{
  "year": 2026,
  "description": "2026 Season"
}
```

---

#### PUT /api/seasons/{item_id}/

Update a season by ID.

**Endpoint:**
```
PUT /api/seasons/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Season ID to update |

**Request Body:**
```json
{
  "description": "Updated 2024 Season",
  "iscurrent": false
}
```

**Request Schema:**
```typescript
interface SeasonSchemaUpdate {
  year: number | null; // Optional - 1900-2999
  description: string | null; // Optional
  iscurrent: boolean | null; // Optional
}
```

**Response (200 OK):**
```json
{
  "id": 2,
  "year": 2024,
  "description": "Updated 2024 Season",
  "iscurrent": false
}
```

**Behavior:**
- Only updates provided fields (partial update)
- If `iscurrent` is set to `true`, all other seasons are automatically set to `iscurrent: false`
- Returns 404 if season not found
- Returns 409 if year is not provided (year is required for updates)

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Season not found |
| 409 | Error updating season - year is required |
| 422 | Validation error - year out of range |
| 500 | Internal server error |

**Example Usage:**
```bash
# Update description only
PUT /api/seasons/2/
{
  "description": "New description"
}

# Set as current season
PUT /api/seasons/2/
{
  "iscurrent": true
}
```

---

#### DELETE /api/seasons/id/{model_id}

Delete a season by ID. Requires admin role. **Warning:** This will cascade delete all tournaments, matches, and related data for this season.

**Endpoint:**
```
DELETE /api/seasons/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | Season ID to delete |

**Response (200 OK):**
```json
{
  "detail": "Season 2 deleted successfully"
}
```

**Behavior:**
- Requires admin role
- **Cascade Delete:** Deleting a season will also delete:
  - All tournaments belonging to this season
  - All matches in those tournaments
  - All team participation records
  - All related statistics
- This is a destructive operation that cannot be undone
- Returns success message even if season doesn't exist (idempotent)

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 500 | Internal server error |

**Important:** Always verify the cascade delete behavior before using this endpoint in production. Consider archiving data instead of deleting if needed for historical records.

---

### Global Settings API Season Endpoints

The Global Settings API provides a simplified interface for basic season CRUD operations. For advanced functionality and specialized queries, use the **Direct Seasons API** documented above.

#### GET /api/settings/seasons/

Get all seasons ordered by year. Returns a simple list without pagination.

**Endpoint:**
```
GET /api/settings/seasons/
```

**Response (200 OK):**
```json
[
  {
    "id": 2,
    "year": 2024,
    "description": "2024 Season",
    "iscurrent": true
  },
  {
    "id": 1,
    "year": 2023,
    "description": "2023 Season",
    "iscurrent": false
  }
]
```

**Response Schema:**
```typescript
interface SeasonSchema {
  id: number;
  year: number; // 1900-2999
  description: string | null;
  iscurrent: boolean;
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

**Use Case:** Simple retrieval of all seasons when pagination is not needed.

---

#### GET /api/settings/seasons/id/{item_id}/

Get a season by ID through the settings API.

**Endpoint:**
```
GET /api/settings/seasons/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Season ID to retrieve |

**Response (200 OK):**
```json
{
  "id": 2,
  "year": 2024,
  "description": "2024 Season",
  "iscurrent": true
}
```

**Response Schema:**
```typescript
interface SeasonSchema {
  id: number;
  year: number; // 1900-2999
  description: string | null;
  iscurrent: boolean;
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Season not found |
| 500 | Internal server error |

**Note:** Equivalent to `GET /api/seasons/id/{item_id}/` in the direct seasons API.

---

#### POST /api/settings/seasons/

Create a new season through the settings API.

**Endpoint:**
```
POST /api/settings/seasons/
```

**Request Body:**
```json
{
  "year": 2024,
  "description": "2024 Season",
  "iscurrent": true
}
```

**Request Schema:**
```typescript
interface SeasonSchemaCreate {
  year: number; // 1900-2999
  description: string | null; // Optional description
  iscurrent: boolean; // Whether this is the current season (default: false)
}
```

**Response (200 OK):**
```json
{
  "id": 2,
  "year": 2024,
  "description": "2024 Season",
  "iscurrent": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 422 | Validation error - invalid request data (e.g., year out of range) |
| 500 | Internal server error |

**Note:** Equivalent to `POST /api/seasons/` in the direct seasons API.

---

#### PUT /api/settings/seasons/{item_id}/

Update a season by ID through the settings API.

**Endpoint:**
```
PUT /api/settings/seasons/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Season ID to update |

**Request Body:**
```json
{
  "description": "Updated 2024 Season",
  "iscurrent": false
}
```

**Request Schema:**
```typescript
interface SeasonSchemaUpdate {
  year: number | null; // Optional - 1900-2999
  description: string | null; // Optional description
  iscurrent: boolean | null; // Optional
}
```

**Response (200 OK):**
```json
{
  "id": 2,
  "year": 2024,
  "description": "Updated 2024 Season",
  "iscurrent": false
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Season not found |
| 422 | Validation error - invalid request data |
| 500 | Internal server error |

**Note:** Similar to `PUT /api/seasons/{item_id}/` but does not require admin role.

---

#### DELETE /api/settings/seasons/id/{model_id}

Delete a season by ID through the settings API.

**Endpoint:**
```
DELETE /api/settings/seasons/id/{model_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | Season ID to delete |

**Response (200 OK):**
```json
{
  "detail": "Season 2 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Season not found |
| 500 | Internal server error |

**Important:** This endpoint performs a cascade delete and will remove all tournaments, matches, and related data for this season. **Use with extreme caution.**

---

### Season Management Best Practices

#### Creating a New Season

**Recommended Approach:**
1. Create the season with `iscurrent: false` first
2. Verify the season was created correctly
3. Set `iscurrent: true` only when ready to switch to the new season
4. This ensures only one season is current at any time

```bash
# Step 1: Create season
POST /api/seasons/
{
  "year": 2025,
  "description": "2025 Season",
  "iscurrent": false
}

# Step 2: Verify creation
GET /api/seasons/year/2025

# Step 3: Set as current when ready
PUT /api/seasons/{new_season_id}/
{
  "iscurrent": true
}
```

#### Switching Current Season

To switch the current season, simply update the desired season's `iscurrent` field to `true`. The system will automatically set all other seasons to `iscurrent: false`.

```bash
PUT /api/seasons/{target_season_id}/
{
  "iscurrent": true
}
```

#### Querying Season-Related Data

For performance and simplicity, use the specialized season endpoints:

| Use Case | Recommended Endpoint |
|----------|-------------------|
| Get tournaments by year | `GET /api/seasons/year/{year}/tournaments` |
| Get tournaments by year and sport | `GET /api/seasons/year/{year}/sports/id/{sport_id}/tournaments` |
| Get teams by year | `GET /api/seasons/year/{year}/teams` |
| Get matches by year | `GET /api/seasons/year/{year}/matches` |
| Get all seasons (simple) | `GET /api/settings/seasons/` |
| Search/Filter seasons | `GET /api/seasons/paginated?search=...` |

#### Season Deletion Considerations

Before deleting a season:
1. Verify no critical data will be lost (cascade delete)
2. Consider archiving instead of deleting for historical records
3. Ensure no active references exist in frontend or other services

**If you must delete:**
```bash
# Delete through direct API (requires admin)
DELETE /api/seasons/id/{season_id}
Authorization: Bearer <admin_token>
```

---
