# Backend API Documentation

Frontend integration guide for StatsBoards Backend APIs and WebSocket endpoints.

## Table of Contents

  - [API Routing Conventions](#api-routing-conventions)
  - [Privacy and User Ownership Filtering](#privacy-and-user-ownership-filtering)
  - [Global Settings API](#global-settings-api)
  - [Seasons API](#seasons-api)
  - [Role API](#role-api)
  - [Auth API](#auth-api)
  - [User API](#user-api)
  - [Person API](#person-api)
  - [Player Search API](#player-search-api)
  - [Player Sport Management API](#player-sport-management-api)
  - [Player Career API](#player-career-api)
 - [Player Detail Context API](#player-detail-context-api)
 - [Sponsors API](#sponsors-api)
 - [Teams in Tournament API](#teams-in-tournament-api)
 - [Available Teams for Tournament API](#available-teams-for-tournament-api)
 - [Available Players for Tournament API](#available-players-for-tournament-api)
 - [Players in Tournament API](#get-apitournamentsidtournament_idplayerspaginated)
 - [Players Without Team in Tournament API](#players-without-team-in-tournament-api)
  - [Available Players for Team in Match API](#available-players-for-team-in-match-api)
  - [Match Stats API](#match-stats-api)
  - [WebSocket Endpoints](#websocket-endpoints)
  - [WebSocket Message Formats](#websocket-message-formats)
  - [WebSocket Troubleshooting Guide](#websocket-troubleshooting-guide)
  - [Player Match API](#player-match-api)
  - [Team Rosters API](#team-rosters-api)
  - [Sports API](#sports-api)
  - [Positions API](#positions-api)
  - [Scoreboards API](#scoreboards-api)
  - [Playclocks API](#playclocks-api)
  - [Gameclocks API](#gameclocks-api)
  - [Football Events API](#football-events-api)
  - [Error Responses](#error-responses)
 - [Integration Examples](#integration-examples)

---

## API Routing Conventions

All base CRUD operations follow consistent routing patterns using path parameters instead of query parameters for resource identification.

### Standard CRUD Routes

| Operation | Route Pattern | Example | Notes |
|-----------|---------------|----------|--------|
| **Create** | `POST /{resource}/` | `POST /api/teams/` | Create new resource with request body |
| **Read All** | `GET /{resource}/` | `GET /api/teams/` | List all resources (supports pagination) |
| **Read By ID** | `GET /{resource}/{item_id}/` | `GET /api/teams/5/` | Get single resource by ID |
| **Update** | `PUT /{resource}/{item_id}/` | `PUT /api/teams/5/` | Update resource by ID with request body |
| **Delete** | `DELETE /{resource}/{item_id}/` | `DELETE /api/users/456/` | Delete resource by ID (custom implementation, not auto-generated) |

### Key Conventions

1. **Path Parameters Only**: All resource IDs are passed as path parameters (`/{item_id}/`), never as query parameters (`?item_id=5`)

2. **Consistent ID Parameter**: Use `{item_id}` as the path parameter name for all base CRUD operations

3. **Trailing Slash**: All routes include trailing slash for consistency

4. **Query Parameters for Filtering**: Query parameters are reserved for filtering, sorting, and pagination (e.g., `?page=1`, `?search=query`)

### Examples

**Correct:**
```bash
PUT /api/teams/5/
GET /api/teams/5/
DELETE /api/users/456/
```

**Incorrect:**
```bash
PUT /api/teams/?item_id=5  # ❌ Query parameter for ID
GET /api/teams/?id=5        # ❌ Query parameter for ID
DELETE /api/teams/?id=5     # ❌ Query parameter for ID
```

### Special Routes

Some endpoints have specialized routes for specific use cases:
- `/id/{item_id}/` - Alternative pattern for GET by ID (e.g., `GET /api/sports/id/5/`)
- `/eesl_id/{eesl_id}/` - Get by external ID (e.g., `GET /api/players/eesl_id/98765`)
- Relation routes - Custom patterns for many-to-many relationships (e.g., `/api/team_in_tournament/{team_id}in{tournament_id}`)

---

## Privacy and User Ownership Filtering

Several resources support privacy settings and user ownership to control access and visibility.

### Supported Resources

The following resources support privacy and user ownership features:

| Resource | Privacy Field | Owner Field |
|-----------|---------------|-------------|
| **Teams** | `isprivate` | `user_id` |
| **Matches** | `isprivate` | `user_id` |
| **Players** | `isprivate` | `user_id` |
| **Tournaments** | `isprivate` | `user_id` |
| **Persons** | `isprivate` | `owner_user_id` |

### Query Parameters for Filtering

All paginated endpoints for these resources support the following optional query parameters:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `user_id` | integer (optional) | Filter resources owned by a specific user. For persons, use `owner_user_id`. | `?user_id=5` |
| `isprivate` | boolean (optional) | Filter by privacy status. `true` for private, `false` for public. | `?isprivate=true` |

### Examples

**Get all public teams:**
```bash
GET /api/teams/paginated?isprivate=false
```

**Get all private matches for user 10:**
```bash
GET /api/matches/paginated?user_id=10&isprivate=true
```

**Get all resources (both public and private) owned by user 3:**
```bash
GET /api/tournaments/paginated?user_id=3
```

**Filter players by owner and combine with existing filters:**
```bash
GET /api/players/paginated/details?sport_id=1&user_id=7&search=John
```

### Notes

- **Default Values**: When creating resources, `isprivate` defaults to `false` (public) and `user_id`/`owner_user_id` defaults to `null` (no owner).
- **Combined Filtering**: Privacy and user ownership filters can be combined with other existing filters like `search`, `week`, `tournament_id`, etc.
- **Ownership Assignment**: Use the `PUT /{resource}/{item_id}/` endpoint to set or update `isprivate` and `user_id`/`owner_user_id` fields.

---

## Global Settings API

Manage global system settings and seasons. These endpoints control application configuration and tournament seasons.

### Settings Endpoints

#### GET /api/settings/grouped

Get all settings grouped by category. Returns organized settings for frontend consumption.

**Endpoint:**
```
GET /api/settings/grouped
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "category": "ui",
      "settings": [
        {
          "id": 1,
          "key": "theme.default",
          "value": "dark",
          "value_type": "string",
          "category": "ui",
          "description": "Default application theme",
          "updated_at": "2024-01-15T10:30:00Z"
        }
      ]
    },
    {
      "category": "notifications",
      "settings": [
        {
          "id": 2,
          "key": "notifications.enabled",
          "value": "true",
          "value_type": "boolean",
          "category": "notifications",
          "description": "Enable email notifications",
          "updated_at": "2024-01-15T11:00:00Z"
        }
      ]
    }
  ]
}
```

**Response Schema:**
```typescript
interface GlobalSettingsGroupedResponse {
  data: GlobalSettingsGroupedSchema[];
}

interface GlobalSettingsGroupedSchema {
  category: string;
  settings: GlobalSettingSchema[];
}

interface GlobalSettingSchema {
  id: number;
  key: string;
  value: string;
  value_type: string;
  category: string | null;
  description: string | null;
  updated_at: string;
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

#### GET /api/settings/category/{category}

Get all settings in a specific category.

**Endpoint:**
```
GET /api/settings/category/{category}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | Yes | Category name to filter settings |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "key": "theme.default",
    "value": "dark",
    "value_type": "string",
    "category": "ui",
    "description": "Default application theme",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

**Response Schema:**
```typescript
interface GlobalSettingSchema {
  id: number;
  key: string;
  value: string;
  value_type: string;
  category: string | null;
  description: string | null;
  updated_at: string;
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

#### GET /api/settings/value/{key}

Get a specific setting value with type conversion. Returns the raw value as a string.

**Endpoint:**
```
GET /api/settings/value/{key}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | string | Yes | Setting key to retrieve |

**Response (200 OK):**
```json
{
  "value": "dark"
}
```

**Response Schema:**
```typescript
interface GlobalSettingValueSchema {
  value: string;
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Setting not found - key does not exist |
| 500 | Internal server error |

---

#### POST /api/settings/

Create a new global setting. Requires admin role.

**Endpoint:**
```
POST /api/settings/
```

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "key": "theme.default",
  "value": "dark",
  "value_type": "string",
  "category": "ui",
  "description": "Default application theme"
}
```

**Request Schema:**
```typescript
interface GlobalSettingSchemaCreate {
  key: string; // Max 100 characters, unique
  value: string;
  value_type: string; // Max 20 characters (e.g., "string", "boolean", "number")
  category: string | null; // Max 50 characters, optional
  description: string | null; // Optional description
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "key": "theme.default",
  "value": "dark",
  "value_type": "string",
  "category": "ui",
  "description": "Default application theme",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 422 | Validation error - invalid request data |
| 500 | Internal server error |

---

#### PUT /api/settings/{item_id}/

Update a global setting by ID. Requires admin role.

**Endpoint:**
```
PUT /api/settings/{item_id}/
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Setting ID to update |

**Request Body:**
```json
{
  "key": "theme.default",
  "value": "light",
  "value_type": "string",
  "category": "ui",
  "description": "Updated default application theme"
}
```

**Request Schema:**
```typescript
interface GlobalSettingSchemaUpdate {
  key: string | null; // Optional - max 100 characters
  value: string | null; // Optional
  value_type: string | null; // Optional - max 20 characters
  category: string | null; // Optional - max 50 characters
  description: string | null; // Optional
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "key": "theme.default",
  "value": "light",
  "value_type": "string",
  "category": "ui",
  "description": "Updated default application theme",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | Setting not found |
| 422 | Validation error - invalid request data |
| 500 | Internal server error |

---

#### DELETE /api/settings/id/{model_id}

Delete a global setting by ID. Requires admin role.

**Endpoint:**
```
DELETE /api/settings/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | Setting ID to delete |

**Response (200 OK):**
```json
{
  "detail": "Setting 1 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 500 | Internal server error |

---

### Season Endpoints

Seasons are managed through the settings API. These endpoints allow CRUD operations for tournament seasons.

#### GET /api/settings/seasons/

Get all seasons ordered by year.

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

---

#### GET /api/settings/seasons/id/{item_id}/

Get a season by ID.

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

---

#### POST /api/settings/seasons/

Create a new season.

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

---

#### PUT /api/settings/seasons/{item_id}/

Update a season by ID.

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

---

#### DELETE /api/settings/seasons/id/{model_id}

Delete a season by ID.

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

---

### Usage Examples

**1. Get grouped settings for frontend:**
```bash
GET /api/settings/grouped
```

**2. Get all UI settings:**
```bash
GET /api/settings/category/ui
```

**3. Get a specific setting value:**
```bash
GET /api/settings/value/theme.default
```

**4. Create a new setting (admin):**
```bash
POST /api/settings/
Authorization: Bearer <token>

{
  "key": "notifications.enabled",
  "value": "true",
  "value_type": "boolean",
  "category": "notifications",
  "description": "Enable email notifications"
}
```

**5. Update a setting (admin):**
```bash
PUT /api/settings/1/
Authorization: Bearer <token>

{
  "value": "light"
}
```

**6. Get all seasons ordered by year:**
```bash
GET /api/settings/seasons/
```

**7. Get the current season:**
```bash
GET /api/settings/seasons/
# Then filter by iscurrent: true on frontend
```

**8. Create a new season:**
```bash
POST /api/settings/seasons/

{
  "year": 2025,
  "description": "2025 Season",
  "iscurrent": true
}
```

---

## Seasons API

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

## Role API

Manage system roles for user authorization. Roles control what users can access and do within the application.

### GET /api/roles/

List all roles with pagination.

**Endpoint:**
```
GET /api/roles/
```

**Query Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number (1-based) | 1 |
| `items_per_page` | integer | No | Items per page (max 100) | 20 |
| `order_by` | string | No | First sort column | `name` |
| `order_by_two` | string | No | Second sort column | `id` |
| `ascending` | boolean | No | Sort order (true=asc, false=desc) | `true` |
| `search` | string | No | Search query for role name | `null` |

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "name": "admin",
      "description": "Administrator with full access",
      "user_count": 3
    },
    {
      "id": 2,
      "name": "user",
      "description": "Basic viewer role",
      "user_count": 45
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
interface Role {
  id: number;
  name: string;
  description: string | null;
  user_count: number;
}

interface PaginatedRoleResponse {
  data: Role[];
  metadata: PaginationMetadata;
}
```

### GET /api/roles/id/{item_id}/

Get a single role by ID.

**Endpoint:**
```
GET /api/roles/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Role ID |

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "admin",
  "description": "Administrator with full access",
  "user_count": 3
}
```

### GET /api/roles/paginated

Search roles by name with pagination and sorting.

**Endpoint:**
```
GET /api/roles/paginated
```

**Query Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number (1-based) | 1 |
| `items_per_page` | integer | No | Items per page (max 100) | 20 |
| `order_by` | string | No | First sort column | `name` |
| `order_by_two` | string | No | Second sort column | `id` |
| `ascending` | boolean | No | Sort order (true=asc, false=desc) | `true` |
| `search` | string | No | Search query for role name (case-insensitive, partial match) | `null` |

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "name": "admin",
      "description": "Administrator with full access",
      "user_count": 3
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
- Search is case-insensitive and uses partial matching (contains)
- Uses ICU collation for consistent international character handling
- `user_count` is dynamically calculated from user_role associations

### POST /api/roles/

Create a new role. Requires admin role.

**Endpoint:**
```
POST /api/roles/
```

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "moderator",
  "description": "Can moderate content and users"
}
```

**Request Schema:**
```typescript
interface RoleCreate {
  name: string; // 2-50 characters, unique
  description: string | null; // Optional
}
```

**Response (200 OK):**
```json
{
  "id": 3,
  "name": "moderator",
  "description": "Can moderate content and users",
  "user_count": 0
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Role with this name already exists |
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 500 | Internal server error |

### PUT /api/roles/{item_id}/

Update role description. Requires admin role.

**Endpoint:**
```
PUT /api/roles/{item_id}/
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Role ID |

**Request Body:**
```json
{
  "description": "Updated role description"
}
```

**Request Schema:**
```typescript
interface RoleUpdate {
  description: string | null; // Optional - only description can be updated
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "admin",
  "description": "Updated role description",
  "user_count": 3
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Role not found |
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 500 | Internal server error |

**Behavior:**
- Only the `description` field can be updated. Role names are immutable to prevent breaking user associations.
- The `user_count` is always included in the response.

### DELETE /api/roles/id/{model_id}

Delete a role. Requires admin role.

**Endpoint:**
```
DELETE /api/roles/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | Role ID |

**Response (200 OK):**
```json
{
  "detail": "ROLE 1 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Cannot delete role - role is assigned to users |
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | Role not found |
| 500 | Internal server error |

**Behavior:**
- Cannot delete roles that have users assigned to them
- Users must be removed from role first (via user role assignment endpoints)
- Prevents accidental deletion of roles in use

---

## Auth API

### POST /api/auth/login

Authenticate a user with username and password. Returns JWT access token.

**Endpoint:**
```
POST /api/auth/login
```

**Request Body:**
```
username=test_user&password=SecurePass123!
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Invalid credentials |

### GET /api/auth/me

Get the currently authenticated user's profile (alias for `/api/users/me`).

**Endpoint:**
```
GET /api/auth/me
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": 456,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "person_id": 123,
  "roles": ["user", "admin"],
  "created": "2024-01-15T10:30:00Z",
  "last_online": "2024-01-15T14:30:00Z",
  "is_online": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 404 | User not found |

### POST /api/auth/heartbeat

Update user's last_online timestamp and set is_online status to true. Used for tracking user activity.

**Endpoint:**
```
POST /api/auth/heartbeat
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response (204 No Content):**

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |

**Behavior:**
- Updates `last_online` timestamp to current UTC time
- Sets `is_online` to `true`
- Should be called periodically by frontend (every 30-60 seconds)
- Background task automatically marks users as offline after 2 minutes of inactivity

---

## User API

### POST /api/users/register

Register a new user account.

**Endpoint:**
```
POST /api/users/register
```

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "person_id": 123
}
```

**Request Schema:**
```typescript
interface UserCreate {
  username: string; // 3-100 characters, unique
  email: string; // Valid email address, unique
  password: string; // Min 6 characters
  person_id: number | null; // Optional person association
}
```

**Response (200 OK):**
```json
{
  "id": 456,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "person_id": 123,
  "roles": ["user", "admin"],
  "created": "2024-01-15T10:30:00Z",
  "last_online": "2024-01-15T14:30:00Z",
  "is_online": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Username or email already exists |
| 500 | Internal server error |

**Behavior:**
- Automatically assigns "user" role to new users
- Password is hashed before storage
- Optional `person_id` can link user to a person record

### GET /api/users/me

Get the currently authenticated user's profile.

**Endpoint:**
```
GET /api/users/me
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": 456,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "person_id": 123,
  "roles": ["user", "admin"]
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 404 | User not found |

### PUT /api/users/me

Update the currently authenticated user's profile.

**Endpoint:**
```
PUT /api/users/me
```

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "is_active": true
}
```

**Request Schema:**
```typescript
interface UserUpdate {
  email: string | null; // Optional new email
  is_active: boolean | null; // Optional active status
}
```

**Response (200 OK):**
```json
{
  "id": 456,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "person_id": 123,
  "roles": ["user"],
  "created": "2024-01-15T10:30:00Z",
  "last_online": null,
  "is_online": false
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 404 | User not found |

**Behavior:**
- Only updates provided fields
- Password is hashed before storage if provided
- Cannot update username (immutable)

### GET /api/users/{user_id}

Get a user by ID with their roles. Requires admin role.

**Endpoint:**
```
GET /api/users/{user_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID to retrieve |

**Response (200 OK):**
```json
{
  "id": 456,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "person_id": 123,
  "roles": ["user", "admin"]
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | User not found |

### PUT /api/users/{user_id}

Update a user by ID. Requires admin role.

**Endpoint:**
```
PUT /api/users/{user_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID to update |

**Request Body:**
```json
{
  "email": "admin@example.com",
  "is_active": false
}
```

**Request Schema:**
```typescript
interface UserUpdate {
  email: string | null; // Optional new email
  is_active: boolean | null; // Optional active status
}
```

**Response (200 OK):**
```json
{
  "id": 456,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "person_id": 123,
  "roles": ["user", "admin"],
  "created": "2024-01-15T10:30:00Z",
  "last_online": "2024-01-15T14:30:00Z",
  "is_online": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | User not found |

**Behavior:**
- Only updates provided fields
- Password is hashed before storage if provided
- Cannot update username (immutable)

### POST /api/users/{user_id}/change-password

Change a user's password without requiring the old password. Requires admin role.

**Endpoint:**
```
POST /api/users/{user_id}/change-password
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID to change password for |

**Request Body:**
```json
{
  "new_password": "NewPassword123!"
}
```

**Request Schema:**
```typescript
interface AdminPasswordChange {
  new_password: string; // Min 6 characters
}
```

**Response (200 OK):**
```json
{
  "id": 456,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "person_id": 123,
  "roles": ["user", "admin"]
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | User not found |

**Behavior:**
- Does not require old password (admin bypass)
- Password is hashed before storage
- Useful for password resets by administrators
 
### POST /api/users/me/change-password

Change the current user's own password. Requires verification of current password.

**Endpoint:**
```
POST /api/users/me/change-password
```

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "old_password": "CurrentPassword123!",
  "new_password": "NewPassword456!"
}
```

**Request Schema:**
```typescript
interface UserChangePassword {
  old_password: string; // Current password (must match)
  new_password: string; // New password (min 6 characters)
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Incorrect password - old password does not match |
| 401 | Unauthorized - missing or invalid token |

**Behavior:**
- Requires current password verification (security measure)
- Password is hashed before storage
- Any authenticated user can use this endpoint

### POST /api/users/{user_id}/roles

Assign a role to a user. Requires admin role.

**Endpoint:**
```
POST /api/users/{user_id}/roles
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID to assign role to |

**Request Body:**
```json
{
  "role_id": 1
}
```

**Request Schema:**
```typescript
interface UserRoleAssign {
  role_id: number;
}
```

**Response (200 OK):**
```json
{
  "id": 456,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "person_id": 123,
  "roles": ["user", "admin"],
  "created": "2024-01-15T10:30:00Z",
  "last_online": "2024-01-15T14:30:00Z",
  "is_online": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | User already has this role |
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | User or role not found |

### DELETE /api/users/{user_id}/roles/{role_id}

Remove a role from a user. Requires admin role.

**Endpoint:**
```
DELETE /api/users/{user_id}/roles/{role_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID |
 | `role_id` | integer | Yes | Role ID to remove |

**Response (200 OK):**
```json
{
  "id": 456,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "person_id": 123,
  "roles": ["user"],
  "created": "2024-01-15T10:30:00Z",
  "last_online": null,
  "is_online": false
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | User does not have this role |
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | User or role not found |

### GET /api/users/{user_id}/roles

Get roles for a user. Requires admin role.

**Endpoint:**
```
GET /api/users/{user_id}/roles
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID |

**Response (200 OK):**
```json
{
  "roles": ["user", "admin"]
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | User not found |

### GET /api/users/search

Search users by username with pagination, ordering, role filtering, and online status filtering.

**Endpoint:**
```
GET /api/users/search
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|----------|-------------|
| `page` | integer | No | 1 | Page number (1-based) |
| `items_per_page` | integer | No | 20 | Items per page (max 100) |
| `order_by` | string | No | "username" | First sort column |
| `order_by_two` | string | No | "id" | Second sort column |
| `ascending` | boolean | No | true | Sort order (true=asc, false=desc) |
| `search` | string | No | - | Search query for username |
| `role_names` | array | No | - | Filter users by role names (e.g., ["admin"]) |
| `is_online` | boolean | No | - | Filter users by online status (true for online users, false for offline users) |

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 456,
      "username": "john_doe",
      "email": "john@example.com",
      "is_active": true,
      "person_id": 123,
      "roles": ["user", "admin"],
      "created": "2024-01-15T10:30:00Z",
      "last_online": "2024-01-15T14:30:00Z",
      "is_online": true
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
interface PaginatedUserResponse {
  data: User[];
  metadata: PaginationMetadata;
}

interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  person_id: number | null;
  roles: string[];
  created: string;
  last_online: string | null;
  is_online: boolean;
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
- Searches `username` field
- Pattern matching: `%query%` (matches anywhere in text)
- `role_names` can be used as query parameter multiple times (e.g., `?role_names=admin&role_names=user`)
- `is_online` filters users by their current online status when provided; when omitted, returns all users regardless of status

**Examples:**

1. **Search users by username:**
```
GET /api/users/search?search=john&page=1&items_per_page=20
```

2. **Filter by role:**
```
GET /api/users/search?role_names=admin&page=1&items_per_page=20
```

3. **Search with role filter:**
```
GET /api/users/search?search=john&role_names=admin&page=1&items_per_page=20
```

4. **Custom ordering:**
```
GET /api/users/search?order_by=is_online&order_by_two=username&ascending=false&page=1&items_per_page=20
```

5. **Filter by online status:**
```
GET /api/users/search?is_online=true&page=1&items_per_page=20
```

6. **Combine filters (online admins):**
```
GET /api/users/search?role_names=admin&is_online=true&page=1&items_per_page=20
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Bad Request - invalid query parameters |
| 500 | Internal Server Error - server error |

### DELETE /api/users/{user_id}

Delete a user by ID. Requires admin role.

**Endpoint:**
```
DELETE /api/users/{user_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID |

**Response (200 OK):**
```json
{
  "detail": "USER 456 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | User not found |
| 500 | Internal server error |

### DELETE /api/users/me

Delete currently authenticated user's account.

**Endpoint:**
```
DELETE /api/users/me
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "detail": "USER deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 404 | User not found |
| 500 | Internal server error |

---

## Person API

### GET /api/persons/not-in-sport/{sport_id}/all

Get all persons not in a specific sport without pagination. This endpoint is designed for dropdown selection when you need all available persons at once.

**Endpoint:**
```
GET /api/persons/not-in-sport/{sport_id}/all
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sport_id` | integer | Yes | Sport ID to filter persons |

**Response (200 OK):**

```json
[
  {
    "id": 123,
    "person_eesl_id": null,
    "first_name": "John",
    "second_name": "Doe",
    "person_photo_url": "/static/uploads/persons/photos/123.jpg",
    "person_photo_icon_url": "/static/uploads/persons/icons/123.jpg",
    "person_photo_web_url": "/static/uploads/persons/web/123.jpg",
    "person_dob": "1990-01-15T00:00:00"
  },
  {
    "id": 124,
    "person_eesl_id": null,
    "first_name": "Jane",
    "second_name": "Smith",
    "person_photo_url": "/static/uploads/persons/photos/124.jpg",
    "person_photo_icon_url": "/static/uploads/persons/icons/124.jpg",
    "person_photo_web_url": "/static/uploads/persons/web/124.jpg",
    "person_dob": "1992-03-22T00:00:00"
  }
]
```

**Response Schema:**

```typescript
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
```

**Behavior:**

- Retrieves all persons who do NOT have a `Player` record with the specified `sport_id`
- No pagination - returns all matching persons in a single response
- No search filtering - simple query without text search
- Empty array returned if no persons match the filter
- Uses SQL `NOT EXISTS` for efficient filtering

**Use Cases:**

- **Person selection dropdown**: When adding players to a sport without pagination
- **Bulk operations**: When you need all available persons for bulk processing
- **Small datasets**: When the total number of persons is manageable without pagination

**Examples:**

1. **Get all persons not in football (sport_id = 1):**
```
GET /api/persons/not-in-sport/1/all
```

2. **Use in dropdown for sport-specific person selection:**
```typescript
async function loadPersonsNotInSport(sportId: number) {
  const response = await fetch(
    `/api/persons/not-in-sport/${sportId}/all`
  );
  const persons: Person[] = await response.json();
  
  // Render dropdown
  return persons.map(person => ({
    value: person.id,
    label: `${person.first_name} ${person.second_name}`,
    avatar: person.person_photo_icon_url
  }));
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - persons returned (empty array if none) |
| 500 | Internal Server Error - server error |

**Note:** Returns empty array (200 OK) if sport doesn't exist or all persons are already in the sport, making it safe for dropdown use cases without requiring error handling.

---

### GET /api/persons/not-in-sport/{sport_id}

Get persons not in a specific sport with pagination, search, and ordering. Use this endpoint when you need pagination or search functionality.

**Endpoint:**
```
GET /api/persons/not-in-sport/{sport_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sport_id` | integer | Yes | Sport ID to filter persons |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|----------|-------------|
| `search` | string | No | - | Search query for first_name or second_name |
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
      "id": 123,
      "person_eesl_id": null,
      "first_name": "John",
      "second_name": "Doe",
      "person_photo_url": "/static/uploads/persons/photos/123.jpg",
      "person_photo_icon_url": "/static/uploads/persons/icons/123.jpg",
      "person_photo_web_url": "/static/uploads/persons/web/123.jpg",
      "person_dob": "1990-01-15T00:00:00"
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
interface PaginatedPersonResponse {
  data: Person[];
  metadata: PaginationMetadata;
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
- Empty `search` parameter returns all persons not in sport
- Default sorting: by `second_name` ascending, then by `id`

**Examples:**

1. **Get paginated persons not in sport:**
```
GET /api/persons/not-in-sport/1?page=1&items_per_page=20
```

2. **Search persons not in sport:**
```
GET /api/persons/not-in-sport/1?search=John&page=1&items_per_page=20
```

3. **Custom ordering:**
```
GET /api/persons/not-in-sport/1?order_by=first_name&ascending=false
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - persons returned |
| 400 | Bad Request - invalid query parameters |
| 500 | Internal Server Error - server error |

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

## Player Sport Management API

### POST /api/players/add-person-to-sport

Add a person to a sport by creating a new Player record. A person can have multiple Player records (one per sport).

**Endpoint:**
```
POST /api/players/add-person-to-sport
```

**Request Body:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|----------|-------------|
| `person_id` | integer | Yes | - | Person ID to add as player |
| `sport_id` | integer | Yes | - | Sport ID to add player to |
| `isprivate` | boolean | No | false | Player privacy flag |
| `user_id` | integer | No | - | User ID associated with player |

**Request Example:**
```json
{
  "person_id": 123,
  "sport_id": 1,
  "isprivate": false,
  "user_id": 5
}
```

**Response (200 OK):**
```json
{
  "id": 456,
  "person_id": 123,
  "sport_id": 1,
  "player_eesl_id": null,
  "isprivate": false,
  "user_id": 5
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - player created |
| 409 | Conflict - player already exists for this person+sport combination |
| 404 | Not Found - person_id or sport_id doesn't exist |
| 500 | Internal Server Error - server error |

### DELETE /api/players/remove-person-from-sport/personid/{person_id}/sportid/{sport_id}

Remove a person from a sport by deleting their Player record. This will cascade delete all related PlayerTeamTournament and PlayerMatch records.

**Endpoint:**
```
DELETE /api/players/remove-person-from-sport/personid/{person_id}/sportid/{sport_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | integer | Yes | Person ID to remove from sport |
| `sport_id` | integer | Yes | Sport ID to remove person from |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Player removed from sport"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - player removed |
| 404 | Not Found - player not found for this person+sport combination |
| 500 | Internal Server Error - server error |

---

## Player Career API

### GET /api/players/id/{player_id}/career

Retrieves player career data pre-grouped by team and tournament/season. This endpoint provides optimized queries with all related data loaded in a single request, eliminating need for frontend grouping logic.

**Endpoint:**
```
GET /api/players/id/{player_id}/career
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `player_id` | integer | Yes | Player ID to fetch career data for |

**Response (200 OK):**

```json
{
  "career_by_team": [
    {
      "team_id": 1,
      "team_title": "FC Barcelona",
      "assignments": [
        {
          "id": 101,
          "team_id": 1,
          "team_title": "FC Barcelona",
          "position_id": 3,
          "position_title": "Forward",
          "player_number": "10",
          "tournament_id": 5,
          "tournament_title": "La Liga 2024",
          "season_id": 2,
          "season_year": 2024
        },
        {
          "id": 102,
          "team_id": 1,
          "team_title": "FC Barcelona",
          "position_id": 3,
          "position_title": "Forward",
          "player_number": "10",
          "tournament_id": 6,
          "tournament_title": "La Liga 2023",
          "season_id": 1,
          "season_year": 2023
        }
      ]
    },
    {
      "team_id": 2,
      "team_title": "Real Madrid",
      "assignments": [
        {
          "id": 103,
          "team_id": 2,
          "team_title": "Real Madrid",
          "position_id": 2,
          "position_title": "Midfielder",
          "player_number": "8",
          "tournament_id": 5,
          "tournament_title": "La Liga 2024",
          "season_id": 2,
          "season_year": 2024
        }
      ]
    }
  ],
  "career_by_tournament": [
    {
      "tournament_id": 5,
      "tournament_title": "La Liga 2024",
      "season_id": 2,
      "season_year": 2024,
      "assignments": [
        {
          "id": 101,
          "team_id": 1,
          "team_title": "FC Barcelona",
          "position_id": 3,
          "position_title": "Forward",
          "player_number": "10",
          "tournament_id": 5,
          "tournament_title": "La Liga 2024",
          "season_id": 2,
          "season_year": 2024
        },
        {
          "id": 103,
          "team_id": 2,
          "team_title": "Real Madrid",
          "position_id": 2,
          "position_title": "Midfielder",
          "player_number": "8",
          "tournament_id": 5,
          "tournament_title": "La Liga 2024",
          "season_id": 2,
          "season_year": 2024
        }
      ]
    },
    {
      "tournament_id": 6,
      "tournament_title": "La Liga 2023",
      "season_id": 1,
      "season_year": 2023,
      "assignments": [
        {
          "id": 102,
          "team_id": 1,
          "team_title": "FC Barcelona",
          "position_id": 3,
          "position_title": "Forward",
          "player_number": "10",
          "tournament_id": 6,
          "tournament_title": "La Liga 2023",
          "season_id": 1,
          "season_year": 2023
        }
      ]
    }
  ]
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `career_by_team` | array | Player assignments grouped by team, sorted alphabetically by team title |
| `career_by_tournament` | array | Player assignments grouped by tournament/season, sorted chronologically (newest first) |
| `career_by_team[].team_id` | integer or null | Team ID |
| `career_by_team[].team_title` | string or null | Team name |
| `career_by_team[].assignments` | array | List of assignments for this team |
| `career_by_tournament[].tournament_id` | integer or null | Tournament ID |
| `career_by_tournament[].tournament_title` | string or null | Tournament name |
| `career_by_tournament[].season_id` | integer or null | Season ID |
| `career_by_tournament[].season_year` | integer or null | Season year |
| `career_by_tournament[].assignments` | array | List of assignments for this tournament/season |
| `assignments[].id` | integer | PlayerTeamTournament record ID |
| `assignments[].team_id` | integer or null | Team ID for this assignment |
| `assignments[].team_title` | string or null | Team name |
| `assignments[].position_id` | integer or null | Position ID |
| `assignments[].position_title` | string or null | Position name |
| `assignments[].player_number` | string or null | Player jersey number |
| `assignments[].tournament_id` | integer or null | Tournament ID |
| `assignments[].tournament_title` | string or null | Tournament name |
| `assignments[].season_id` | integer or null | Season ID |
| `assignments[].season_year` | integer or null | Season year |

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - career data returned |
| 404 | Not Found - player_id doesn't exist |
| 500 | Internal Server Error - server error |

**Notes:**

- All relationships (team, position, tournament, season) are loaded in a single optimized query
- `career_by_team` is sorted alphabetically by team title
- `career_by_tournament` is sorted chronologically by season year (newest first)
- Empty arrays are returned for players with no team/tournament assignments
- Use this endpoint instead of manually grouping `player_team_tournaments` on frontend

**Related Issues:**
- STAB-67: Add Player Career Endpoint
- STAB-68: Implement Career Grouping Service Method
- STAB-69: Add Career Grouping Schemas
 - STAB-70: Backend Player Career API (parent)
 
---

## Player Detail Context API

These endpoints provide player details with context-specific data based on where the player is being viewed from (sport, tournament, team, or match). Each endpoint returns person data with photos, sport info, relevant context assignment, and full career data in a single optimized API call.

### GET /api/players/id/{player_id}/in-tournament/{tournament_id}

Get player details in tournament context. Returns person with photos, sport info, specific tournament assignment (team, position, player number), and full career data.

**Endpoint:**
```
GET /api/players/id/{player_id}/in-tournament/{tournament_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `player_id` | integer | Yes | Player ID to fetch details for |
| `tournament_id` | integer | Yes | Tournament ID context |

**Response (200 OK):**
```json
{
  "id": 1,
  "sport_id": 1,
  "person": {
    "id": 123,
    "person_eesl_id": null,
    "first_name": "John",
    "second_name": "Doe",
    "person_photo_url": "/static/uploads/persons/photos/123.jpg",
    "person_photo_icon_url": "/static/uploads/persons/icons/123.jpg",
    "person_photo_web_url": "/static/uploads/persons/web/123.jpg",
    "person_dob": "1990-01-15T00:00:00"
  },
  "sport": {
    "id": 1,
    "title": "Football"
  },
  "tournament_assignment": {
    "team_id": 5,
    "team_title": "FC Barcelona",
    "position_id": 3,
    "position_title": "Forward",
    "player_number": "10",
    "tournament_title": "La Liga 2024",
    "tournament_year": "2024",
    "tournament_id": 2
  },
  "career_by_team": [
    {
      "team_id": 5,
      "team_title": "FC Barcelona",
      "assignments": [
        {
          "id": 101,
          "team_id": 5,
          "team_title": "FC Barcelona",
          "position_id": 3,
          "position_title": "Forward",
          "player_number": "10",
          "tournament_id": 2,
          "tournament_title": "La Liga 2024",
          "season_id": 2,
          "season_year": 2024
        }
      ]
    }
  ],
  "career_by_tournament": [
    {
      "tournament_id": 2,
      "tournament_title": "La Liga 2024",
      "season_id": 2,
      "season_year": 2024,
      "assignments": [
        {
          "id": 101,
          "team_id": 5,
          "team_title": "FC Barcelona",
          "position_id": 3,
          "position_title": "Forward",
          "player_number": "10",
          "tournament_id": 2,
          "tournament_title": "La Liga 2024",
          "season_id": 2,
          "season_year": 2024
        }
      ]
    }
  ]
}
```

**Response Schema:**

```typescript
interface PlayerDetailInTournamentResponse {
  id: number;
  sport_id: number;
  person: Person;
  sport: Sport;
  tournament_assignment: TournamentAssignment;
  career_by_team: CareerByTeam[];
  career_by_tournament: CareerByTournament[];
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

interface Sport {
  id: number;
  title: string;
}

interface TournamentAssignment {
  team_id: number | null;
  team_title: string | null;
  position_id: number | null;
  position_title: string | null;
  player_number: string | null;
  tournament_title: string | null;
  tournament_year: string | null;
  tournament_id: number | null;
}

interface CareerByTeam {
  team_id: number | null;
  team_title: string | null;
  assignments: TeamAssignment[];
}

interface CareerByTournament {
  tournament_id: number | null;
  tournament_title: string | null;
  season_id: number | null;
  season_year: number | null;
  assignments: TeamAssignment[];
}

interface TeamAssignment {
  id: number;
  team_id: number | null;
  team_title: string | null;
  position_id: number | null;
  position_title: string | null;
  player_number: string | null;
  tournament_id: number | null;
  tournament_title: string | null;
  season_id: number | null;
  season_year: number | null;
}
```

**Behavior:**

- Returns player details with person (including photos) and sport information
- Includes specific tournament assignment for the given tournament context
- Includes full career data grouped by team and by tournament/season
- All relationships (person, sport, team, position, tournament, season) are loaded in a single optimized query
- Player must exist and must be assigned to the specified tournament
- `career_by_team` is sorted alphabetically by team title
- `career_by_tournament` is sorted chronologically by season year (newest first)

**Use Cases:**

- **Player detail page from tournament view**: Display player information when navigating from tournament roster
- **Tournament context player details**: Show player's specific role and assignment in that tournament
- **Optimized single API call**: Replace multiple calls (person + career) with one optimized endpoint

**Examples:**

1. **Get player details in tournament context:**
```
GET /api/players/id/1/in-tournament/2
```

2. **Display tournament player details:**
```typescript
async function loadPlayerDetailInTournament(playerId: number, tournamentId: number) {
  const response = await fetch(
    `/api/players/id/${playerId}/in-tournament/${tournamentId}`
  );
  const data: PlayerDetailInTournamentResponse = await response.json();
  
  return {
    player: data.person,
    sport: data.sport,
    tournamentContext: data.tournament_assignment,
    career: {
      byTeam: data.career_by_team,
      byTournament: data.career_by_tournament
    }
  };
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - player details returned |
| 404 | Not Found - player_id doesn't exist OR player not assigned to tournament_id |
| 500 | Internal Server Error - server error |

**Notes:**

- This is a PRIORITY endpoint for player detail views accessed from tournament pages
- Replaces the need for calling `/api/players/id/{player_id}/person` AND `/api/players/id/{player_id}/career` separately
- Frontend can use a single component with context-aware routing
- See [Player Career API](#player-career-api) for details on career data structure

**Related Issues:**

- STAB-79: Create context-specific backend endpoints for player detail (parent)
 
---

## Sponsors API

Manage sponsors for tournaments and matches. Sponsors can be linked to sponsor lines and displayed on various tournament views.

### Sponsor Schema

Base schema for all sponsor-related operations.

```typescript
interface SponsorSchema {
  id: number;
  title: string; // Max 50 characters
  logo_url: string | null; // URL to sponsor logo image
  scale_logo: number | null; // Scale factor for logo display (default: 1.0)
}
```

### POST /api/sponsors/

Create a new sponsor.

**Endpoint:**
```
POST /api/sponsors/
```

**Request Body:**
```json
{
  "title": "Acme Corp",
  "logo_url": "/static/uploads/sponsors/logos/acme.png",
  "scale_logo": 1.5
}
```

**Request Schema:**
```typescript
interface SponsorSchemaCreate {
  title: string; // Max 50 characters
  logo_url: string | null; // Optional - logo URL (default: empty string)
  scale_logo: number | null; // Optional - scale factor (default: 1.0)
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Acme Corp",
  "logo_url": "/static/uploads/sponsors/logos/acme.png",
  "scale_logo": 1.5
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 409 | Conflict - Failed to create sponsor, check input data |
| 500 | Internal Server Error - server error |

### PUT /api/sponsors/{item_id}/

Update a sponsor by ID.

**Endpoint:**
```
PUT /api/sponsors/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Sponsor ID to update |

**Request Body:**
```json
{
  "title": "Updated Acme Corp",
  "logo_url": "/static/uploads/sponsors/logos/acme-updated.png",
  "scale_logo": 2.0
}
```

**Request Schema:**
```typescript
interface SponsorSchemaUpdate {
  title: string | null; // Optional - Max 50 characters
  logo_url: string | null; // Optional
  scale_logo: number | null; // Optional
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Updated Acme Corp",
  "logo_url": "/static/uploads/sponsors/logos/acme-updated.png",
  "scale_logo": 2.0
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Not Found - Sponsor with specified ID not found |
| 500 | Internal Server Error - server error |

### GET /api/sponsors/id/{item_id}/

Get a single sponsor by ID.

**Endpoint:**
```
GET /api/sponsors/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Sponsor ID to retrieve |

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "title": "Acme Corp",
      "logo_url": "/static/uploads/sponsors/logos/acme.png",
      "scale_logo": 1.5
    }
  ],
  "title": "Sponsor ID: 1",
  "item_type": "Sponsor"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Not Found - Sponsor with specified ID not found |
| 500 | Internal Server Error - server error |

### POST /api/sponsors/upload_logo

Upload a sponsor logo image. Returns the URL of the uploaded file.

**Endpoint:**
```
POST /api/sponsors/upload_logo
```

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body:** `file` (UploadFile) - The logo image file to upload

**Supported File Types:** Image files (validated by file service)
- Storage location: `/static/uploads/sponsors/logos/`

**Response (200 OK):**
```json
{
  "logoUrl": "/static/uploads/sponsors/logos/acme.png"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal Server Error - Error uploading sponsor logo |

**Usage Example:**

```typescript
async function uploadSponsorLogo(file: File): Promise<string> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/sponsors/upload_logo', {
    method: 'POST',
    body: formData,
  });

  const result = await response.json();
  return result.logoUrl;
}
```

### GET /api/sponsors/paginated

Search sponsors with pagination and sorting.

**Endpoint:**
```
GET /api/sponsors/paginated
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|----------|-------------|
| `page` | integer | No | 1 | Page number (1-based) |
| `items_per_page` | integer | No | 20 | Items per page (max 100) |
| `order_by` | string | No | "title" | First sort column |
| `order_by_two` | string | No | "id" | Second sort column |
| `ascending` | boolean | No | true | Sort order (true=asc, false=desc) |
| `search` | string | No | - | Search query for title search |

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "title": "Acme Corp",
      "logo_url": "/static/uploads/sponsors/logos/acme.png",
      "scale_logo": 1.5
    },
    {
      "id": 2,
      "title": "Beta Industries",
      "logo_url": "/static/uploads/sponsors/logos/beta.png",
      "scale_logo": 1.0
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
interface PaginatedSponsorResponse {
  data: SponsorSchema[];
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

**Search Behavior:**

- Search is case-insensitive and matches anywhere in title
- Empty `search` parameter returns all sponsors
- Default sorting: by `title` ascending, then by `id`

**Examples:**

1. **Get all sponsors with pagination:**
```
GET /api/sponsors/paginated?page=1&items_per_page=20
```

2. **Search sponsors by title:**
```
GET /api/sponsors/paginated?search=Acme&page=1&items_per_page=20
```

3. **Custom ordering:**
```
GET /api/sponsors/paginated?order_by=title&order_by_two=id&ascending=false
```

### DELETE /api/sponsors/id/{model_id}

Delete a sponsor by ID. Requires admin role.

**Endpoint:**
```
DELETE /api/sponsors/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | Sponsor ID to delete |

**Response (200 OK):**
```json
{
  "detail": "Sponsor 1 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - requires admin role |
| 500 | Internal Server Error - server error |

---

## Sponsor Lines API

Manage sponsor lines for organizing and grouping sponsors. Sponsor lines can contain multiple sponsors and are used for display organization.

### Sponsor Line Schema

Base schema for all sponsor line operations.

```typescript
interface SponsorLineSchema {
  id: number;
  title: string; // Max 50 characters (default: "Sponsor Line")
  is_visible: boolean | null; // Visibility flag (default: false)
}
```

### POST /api/sponsor_lines/

Create a new sponsor line.

**Endpoint:**
```
POST /api/sponsor_lines/
```

**Request Body:**
```json
{
  "title": "Premier Sponsors",
  "is_visible": true
}
```

**Request Schema:**
```typescript
interface SponsorLineSchemaCreate {
  title: string; // Max 50 characters (default: "Sponsor Line")
  is_visible: boolean | null; // Optional (default: false)
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Premier Sponsors",
  "is_visible": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 409 | Conflict - Error creating sponsor line |
| 500 | Internal Server Error - server error |

### PUT /api/sponsor_lines/{item_id}/

Update a sponsor line by ID.

**Endpoint:**
```
PUT /api/sponsor_lines/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Sponsor line ID to update |

**Request Body:**
```json
{
  "title": "Updated Premier Sponsors",
  "is_visible": false
}
```

**Request Schema:**
```typescript
interface SponsorLineSchemaUpdate {
  title: string | null; // Optional - Max 50 characters
  is_visible: boolean | null; // Optional
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Updated Premier Sponsors",
  "is_visible": false
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Not Found - Sponsor line with specified ID not found |
| 409 | Conflict - Error updating sponsor line |
| 500 | Internal Server Error - server error |

### GET /api/sponsor_lines/id/{item_id}/

Get a single sponsor line by ID.

**Endpoint:**
```
GET /api/sponsor_lines/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Sponsor line ID to retrieve |

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "title": "Premier Sponsors",
      "is_visible": true
    }
  ],
  "title": "SponsorLine ID: 1",
  "item_type": "SponsorLine"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Not Found - Sponsor line with specified ID not found |
| 500 | Internal Server Error - server error |

### DELETE /api/sponsor_lines/id/{model_id}

Delete a sponsor line by ID. Requires admin role.

**Endpoint:**
```
DELETE /api/sponsor_lines/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | Sponsor line ID to delete |

**Response (200 OK):**
```json
{
  "detail": "SponsorLine 1 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - requires admin role |
| 500 | Internal Server Error - server error |

---

## Sponsor-Sponsor Line Connection API

Manage many-to-many relationships between sponsors and sponsor lines. Each sponsor can be associated with multiple sponsor lines, and each line can contain multiple sponsors.

### Sponsor-Sponsor Line Schema

Base schema for connection operations.

```typescript
interface SponsorSponsorLineSchema {
  id: number;
  sponsor_id: number; // Sponsor ID
  sponsor_line_id: number; // Sponsor line ID
  position: number | null; // Display position within the line (default: 1)
}
```

### POST /api/sponsor_in_sponsor_line/{sponsor_id}in{sponsor_line_id}

Create a connection between a sponsor and a sponsor line.

**Endpoint:**
```
POST /api/sponsor_in_sponsor_line/{sponsor_id}in{sponsor_line_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sponsor_id` | integer | Yes | Sponsor ID to connect |
| `sponsor_line_id` | integer | Yes | Sponsor line ID to connect to |

**Response (200 OK):**
```json
{
  "id": 1,
  "sponsor_id": 1,
  "sponsor_line_id": 1,
  "position": 1
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 409 | Conflict - Relation already exists or failed to create |
| 500 | Internal Server Error - server error |

**Note:**
- If the relation already exists, the endpoint returns a 409 status
- Default position is 1 if not specified in the service layer

### PUT /api/sponsor_in_sponsor_line/{item_id}/

Update a sponsor-sponsor line connection by ID.

**Endpoint:**
```
PUT /api/sponsor_in_sponsor_line/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Connection ID to update |

**Request Body:**
```json
{
  "sponsor_id": 2,
  "sponsor_line_id": 1,
  "position": 3
}
```

**Request Schema:**
```typescript
interface SponsorSponsorLineSchemaUpdate {
  sponsor_id: number | null; // Optional
  sponsor_line_id: number | null; // Optional
  position: number | null; // Optional
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "sponsor_id": 2,
  "sponsor_line_id": 1,
  "position": 3
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Not Found - Connection with specified ID not found |
| 409 | Conflict - Error updating connection |
| 500 | Internal Server Error - server error |

### GET /api/sponsor_in_sponsor_line/{sponsor_id}in{sponsor_line_id}

Get a specific sponsor-sponsor line connection.

**Endpoint:**
```
GET /api/sponsor_in_sponsor_line/{sponsor_id}in{sponsor_line_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sponsor_id` | integer | Yes | Sponsor ID |
| `sponsor_line_id` | integer | Yes | Sponsor line ID |

**Response (200 OK):**
```json
{
  "id": 1,
  "sponsor_id": 1,
  "sponsor_line_id": 1,
  "position": 1
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Not Found - Connection not found |
| 500 | Internal Server Error - server error |

### GET /api/sponsor_in_sponsor_line/sponsor_line/id/{sponsor_line_id}/sponsors

Get all sponsors associated with a specific sponsor line.

**Endpoint:**
```
GET /api/sponsor_in_sponsor_line/sponsor_line/id/{sponsor_line_id}/sponsors
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sponsor_line_id` | integer | Yes | Sponsor line ID to get sponsors for |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Acme Corp",
    "logo_url": "/static/uploads/sponsors/logos/acme.png",
    "scale_logo": 1.5
  },
  {
    "id": 2,
    "title": "Beta Industries",
    "logo_url": "/static/uploads/sponsors/logos/beta.png",
    "scale_logo": 1.0
  }
]
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal Server Error - server error |

**Usage Example:**

```typescript
async function getSponsorsInLine(sponsorLineId: number): Promise<Sponsor[]> {
  const response = await fetch(
    `/api/sponsor_in_sponsor_line/sponsor_line/id/${sponsorLineId}/sponsors`
  );
  return await response.json();
}
```

### DELETE /api/sponsor_in_sponsor_line/{sponsor_id}in{sponsor_line_id}

Delete a specific sponsor-sponsor line connection.

**Endpoint:**
```
DELETE /api/sponsor_in_sponsor_line/{sponsor_id}in{sponsor_line_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sponsor_id` | integer | Yes | Sponsor ID in the connection |
| `sponsor_line_id` | integer | Yes | Sponsor line ID in the connection |

**Response (204 No Content):**

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal Server Error - server error |

---

## Teams in Tournament API

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

## Available Teams for Tournament API

### GET /api/tournaments/id/{tournament_id}/teams/available

Get all teams in a tournament's sport who are not already connected to the tournament. This endpoint is designed for dropdown selection of available teams to add to a tournament.

**Endpoint:**
```
GET /api/tournaments/id/{tournament_id}/teams/available
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
    "title": "Team Alpha",
    "city": "Boston",
    "description": "Professional sports team",
    "team_logo_url": "/static/uploads/teams/logos/1.jpg",
    "team_logo_icon_url": "/static/uploads/teams/icons/1.jpg",
    "team_logo_web_url": "/static/uploads/teams/web/1.jpg",
    "team_color": "#FF0000",
    "sponsor_line_id": null,
    "main_sponsor_id": 5,
    "sport_id": 1
  },
  {
    "id": 2,
    "team_eesl_id": 12346,
    "title": "Team Beta",
    "city": "New York",
    "description": "Another sports team",
    "team_logo_url": "/static/uploads/teams/logos/2.jpg",
    "team_logo_icon_url": "/static/uploads/teams/icons/2.jpg",
    "team_logo_web_url": "/static/uploads/teams/web/2.jpg",
    "team_color": "#0000FF",
    "sponsor_line_id": null,
    "main_sponsor_id": 6,
    "sport_id": 1
  }
]
```

**Response Schema:**

```typescript
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
```

**Behavior:**

- Retrieves all teams whose `sport_id` matches the tournament's `sport_id`
- Excludes teams who already have a `TeamTournament` connection to this tournament
- Returns teams sorted by `title` (alphabetical order)
- Returns empty array if tournament doesn't exist or no available teams
- No pagination - returns all matching teams in a single response

**Use Cases:**

- **Team selection dropdown**: When adding teams to a tournament
- **Tournament administration**: Finding eligible teams to join tournament
- **Tournament setup**: Selecting teams from the sport to participate

**Examples:**

1. **Get available teams for tournament:**
```
GET /api/tournaments/id/5/teams/available
```

2. **Use in dropdown for adding teams:**
```typescript
async function loadAvailableTeams(tournamentId: number) {
  const response = await fetch(
    `/api/tournaments/id/${tournamentId}/teams/available`
  );
  const teams: Team[] = await response.json();
  
  // Render dropdown
  return teams.map(team => ({
    value: team.id,
    label: team.title,
    logo: team.team_logo_icon_url
  }));
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - available teams returned (empty array if none) |
| 500 | Internal Server Error - server error |

**Note:** Returns empty array (200 OK) instead of 404 if tournament doesn't exist, making it safe for dropdown use cases.

---

## Players in Tournament API

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

## Available Players for Tournament API

### GET /api/tournaments/id/{tournament_id}/players/available

Get all players in a tournament's sport who are not already connected to the tournament. This endpoint is designed for dropdown selection of available players to add to a tournament.

**Endpoint:**
```
GET /api/tournaments/id/{tournament_id}/players/available
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
  {
    "id": 790,
    "sport_id": 1,
    "person_id": 124,
    "player_eesl_id": 98766,
    "person": {
      "id": 124,
      "person_eesl_id": null,
      "first_name": "Jane",
      "second_name": "Smith",
      "person_photo_url": "/static/uploads/persons/photos/124.jpg",
      "person_photo_icon_url": "/static/uploads/persons/icons/124.jpg",
      "person_photo_web_url": "/static/uploads/persons/web/124.jpg",
      "person_dob": "1992-03-22T00:00:00"
    }
  }
]
```

**Response Schema:**

```typescript
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
```

**Behavior:**

- Retrieves all players whose `sport_id` matches tournament's `sport_id`
- Excludes players who already have a `PlayerTeamTournament` connection to this tournament
- Returns players with person details pre-loaded for efficient dropdown display
- Results are sorted by player name (second_name, then first_name) in ascending alphabetical order
- Returns empty array if tournament doesn't exist or no available players

**Use Cases:**

- **Player selection dropdown**: When adding players to a tournament roster
- **Roster management**: When adding new players to a tournament without duplicates
- **Tournament administration**: Finding eligible players to join tournament

**Examples:**

1. **Get available players for tournament:**
```
GET /api/tournaments/id/5/players/available
```

2. **Use in dropdown for adding players:**
```typescript
async function loadAvailablePlayers(tournamentId: number) {
  const response = await fetch(
    `/api/tournaments/id/${tournamentId}/players/available`
  );
  const players: PlayerWithPerson[] = await response.json();
  
  // Render dropdown
  return players.map(player => ({
    value: player.id,
    label: `${player.person.first_name} ${player.person.second_name}`,
    avatar: player.person.person_photo_icon_url
  }));
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - available players returned (empty array if none) |
| 500 | Internal Server Error - server error |

**Note:** Returns empty array (200 OK) instead of 404 if tournament doesn't exist, making it safe for dropdown use cases.

---

## Players Without Team in Tournament API

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

## Available Players for Team in Match API

### GET /api/matches/id/{match_id}/team/{team_id}/available-players/

Get all players in a team's tournament roster who are not already connected to a specific match. This endpoint is designed for dropdown selection of available players when adding players to a match roster.

**Endpoint:**
```
GET /api/matches/id/{match_id}/team/{team_id}/available-players/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID |
| `team_id` | integer | Yes | Team ID |

**Response (200 OK):**

```json
[
  {
    "id": 789,
    "player_id": 791,
    "player_team_tournament": {
      "id": 789,
      "player_team_tournament_eesl_id": null,
      "player_id": 791,
      "position_id": 10,
      "team_id": 1,
      "tournament_id": 5,
      "player_number": "8"
    },
    "player": {
      "id": 791,
      "sport_id": 1,
      "person_id": 125,
      "player_eesl_id": 12347
    },
    "person": {
      "id": 125,
      "person_eesl_id": null,
      "first_name": "Backup",
      "second_name": "Quarterback",
      "person_photo_url": "/static/uploads/persons/photos/125.jpg",
      "person_photo_icon_url": "/static/uploads/persons/icons/125.jpg",
      "person_photo_web_url": "/static/uploads/persons/web/125.jpg",
      "person_dob": "1995-06-15T00:00:00"
    },
    "position": {
      "id": 10,
      "title": "Quarterback",
      "category": "offense",
      "sport_id": 1
    },
    "team": {
      "id": 1,
      "team_eesl_id": 12345,
      "title": "Team A",
      "city": "Boston",
      "description": "Professional football team",
      "team_logo_url": "/static/uploads/teams/logos/1.jpg",
      "team_logo_icon_url": "/static/uploads/teams/icons/1.jpg",
      "team_logo_web_url": "/static/uploads/teams/web/1.jpg",
      "team_color": "#FF0000",
      "sponsor_line_id": null,
      "main_sponsor_id": 5,
      "sport_id": 1
    },
    "player_number": "8"
  }
]
```

**Response Schema:**

```typescript
interface AvailablePlayerMatch {
  id: number;
  player_id: number | null;
  player_team_tournament: PlayerTeamTournament;
  player: Player | null;
  person: Person | null;
  position: Position | null;
  team: Team | null;
  player_number: string;
}

interface PlayerTeamTournament {
  id: number;
  player_team_tournament_eesl_id: number | null;
  player_id: number | null;
  position_id: number | null;
  team_id: number | null;
  tournament_id: number | null;
  player_number: string;
}

interface Player {
  id: number;
  sport_id: number | null;
  person_id: number | null;
  player_eesl_id: number | null;
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

interface Position {
  id: number;
  title: string;
  category: 'offense' | 'defense' | 'special' | 'other' | null;
  sport_id: number;
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
```

**Behavior:**

- Retrieves all `PlayerTeamTournament` records matching the team_id and match's tournament_id
- Excludes players who already have a `PlayerMatch` connection to this match
- Returns players with full related data: player, person, position, team
- Returns empty array if match doesn't exist or no available players
- Designed for efficient dropdown rendering with all necessary data pre-loaded

**Use Cases:**

- **Player selection dropdown**: When adding players to a match roster
- **Substitution management**: Finding bench players available for substitution
- **Match administration**: Managing match rosters by adding/removing players

**Examples:**

1. **Get available players for team in match:**
```
GET /api/matches/id/123/team/1/available-players/
```

2. **Use in dropdown for adding players to match:**
```typescript
async function loadAvailablePlayers(matchId: number, teamId: number) {
  const response = await fetch(
    `/api/matches/id/${matchId}/team/${teamId}/available-players/`
  );
  const players: AvailablePlayerMatch[] = await response.json();
  
  // Render dropdown
  return players.map(player => ({
    value: player.player_team_tournament.id,
    label: `${player.person?.first_name} ${player.person?.second_name} (${player.player_number})`,
    avatar: player.person?.person_photo_icon_url,
    position: player.position?.title
  }));
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - available players returned (empty array if none) |
| 404 | Not Found - match doesn't exist |
| 500 | Internal Server Error - server error |

**Note:** Returns empty array (200 OK) instead of 404 if match doesn't exist, making it safe for dropdown use cases without requiring error handling.

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

## WebSocket Endpoints

### Overview

The backend provides real-time data streaming through WebSocket connections for:
- Live match data updates (scores, game clock, play clock, events)
- Match statistics with conflict resolution
- Real-time scoreboard and clock synchronization

**Important Note:** WebSocket endpoints in `README.md` are outdated. The current actual endpoints are:

| README URL | Actual URL | Status |
|-------------|--------------|--------|
| `ws://localhost:9000/ws/matchdata/{match_id}` | `/api/matches/ws/id/{match_id}/{client_id}/` | ⚠️ Outdated |
| `ws://localhost:9000/ws/scoreboard/{scoreboard_id}` | Does not exist | ⚠️ Outdated |

### WebSocket Endpoint 1: Match Data

Real-time match data streaming including scores, game clock, play clock, and football events.

#### Connection

```typescript
const ws = new WebSocket('ws://localhost:9000/api/matches/ws/id/{match_id}/{client_id}/');
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID to subscribe to |
| `client_id` | string | Yes | Unique client identifier (use UUID or user-specific ID) |

#### Authentication

**Current Status:** No authentication required

Future versions may implement WebSocket authentication through:
- Query parameters: `?token=jwt_token`
- Subprotocol headers

#### Initial Data

Upon successful connection, the server sends three initial messages immediately:

```typescript
// 1. Match data update
{
  "type": "message-update",
  "match_id": 123,
  "match": {
    "id": 123,
    "title": "Team A vs Team B",
    "match_date": "2026-01-21T19:00:00Z",
    "team_a_id": 1,
    "team_b_id": 2,
    "team_a_score": 14,
    "team_b_score": 10
  },
  "teams_data": {
    "team_a": {
      "id": 1,
      "title": "Team A",
      "team_color": "#FF0000",
      "logo_url": "/static/uploads/teams/logos/1.jpg"
    },
    "team_b": {
      "id": 2,
      "title": "Team B",
      "team_color": "#0000FF",
      "logo_url": "/static/uploads/teams/logos/2.jpg"
    }
  },
  "match_data": {
    "id": 456,
    "match_id": 123,
    "field_length": 92,
    "game_status": "in-progress",
    "score_team_a": 14,
    "score_team_b": 10,
    "timeout_team_a": "●●",
    "timeout_team_b": "●●",
    "qtr": "1st",
    "ball_on": 20,
    "down": "1st",
    "distance": "10"
  },
  "scoreboard_data": {
    "id": 789,
    "match_id": 123,
    "is_qtr": true,
    "is_time": true,
    "is_playclock": true,
    "is_downdistance": true,
    "team_a_game_color": "#FF0000",
    "team_b_game_color": "#0000FF",
    "team_a_game_title": "Team A",
    "team_b_game_title": "Team B"
  }
}

// 2. Playclock update
{
  "type": "playclock-update",
  "match_id": 123,
  "playclock": {
    "id": 234,
    "match_id": 123,
    "playclock": 40,
    "playclock_status": "running"
  }
}

// 3. Gameclock update
{
  "type": "gameclock-update",
  "match_id": 123,
  "gameclock": {
    "id": 345,
    "match_id": 123,
    "gameclock": 720,
    "gameclock_max": 720,
    "gameclock_status": "stopped"
  }
}
```

#### Server-Sent Messages

The following message types are sent from server to client when data changes:

| Message Type | Trigger | Description |
|--------------|----------|-------------|
| `match-update` | Match data changes | Updated match information, teams, or scoreboard |
| `message-update` | Match data changes | Initial message with full match context |
| `gameclock-update` | Game clock changes | Updated game clock time or status |
| `playclock-update` | Play clock changes | Updated play clock time or status |
| `event-update` | Football events occur | New or updated football events |

##### Match Update Message

```typescript
interface MatchUpdateMessage {
  type: "match-update" | "message-update";
  match_id: number;
  match: MatchData;
  teams_data: {
    team_a: TeamData;
    team_b: TeamData;
  };
  match_data: {
    id: number;
    match_id: number;
    field_length?: number;
    game_status?: string;  // "in-progress", "stopped", "completed"
    score_team_a?: number;
    score_team_b?: number;
    timeout_team_a?: string;
    timeout_team_b?: string;
    qtr?: string;
    ball_on?: number;
    down?: string;
    distance?: string;
  };
  scoreboard_data?: ScoreboardData;
}

interface TeamData {
  id: number;
  title: string;
  team_color: string;
  logo_url?: string;
}

interface ScoreboardData {
  id: number;
  match_id: number;
  is_qtr: boolean;
  is_time: boolean;
  is_playclock: boolean;
  is_downdistance: boolean;
  is_tournament_logo: boolean;
  team_a_game_color: string;
  team_b_game_color: string;
  team_a_game_title?: string;
  team_b_game_title?: string;
  // ... additional scoreboard fields
}
```

##### Gameclock Update Message

```typescript
interface GameclockUpdateMessage {
  type: "gameclock-update";
  match_id: number;
  gameclock: {
    id: number;
    match_id: number;
    gameclock: number;
    gameclock_max?: number;
    gameclock_status: string;  // "stopped", "running", "paused"
    gameclock_time_remaining?: number;
  };
}
```

##### Playclock Update Message

```typescript
interface PlayclockUpdateMessage {
  type: "playclock-update";
  match_id: number;
  playclock: {
    id: number;
    match_id: number;
    playclock?: number;
    playclock_status: string;  // "stopped", "running"
  };
}
```

##### Event Update Message

```typescript
interface EventUpdateMessage {
  type: "event-update";
  match_id: number;
  events: FootballEvent[];
}

interface FootballEvent {
  id: number;
  match_id: number;
  quarter: string;
  time_remaining: string;
  event_type: string;
  description?: string;
  player_id?: number;
  player?: {
    id: number;
    person: {
      first_name: string;
      last_name: string;
    };
  };
}
```

#### PostgreSQL NOTIFY/LISTEN Mechanism

The backend uses PostgreSQL's `NOTIFY`/`LISTEN` mechanism for real-time updates:

**Channels:**
- `matchdata_change` - Match data updates
- `match_change` - Match information updates
- `scoreboard_change` - Scoreboard updates
- `playclock_change` - Play clock updates
- `gameclock_change` - Game clock updates
- `football_event_change` - Football event updates

**How It Works:**
1. Database triggers send `NOTIFY` messages when relevant data changes
2. WebSocket manager listens for these notifications
3. Matched clients receive updates via their queues

#### Connection Lifecycle

```
Client                              Server
  |                                   |
  |----- CONNECT ---------------------->|  Client connects with match_id and client_id
  |                                   |
  |<---- message-update ------------|  Send full match context data
  |<---- playclock-update ----------|
  |<---- gameclock-update ---------|
  |                                   |
  |<---- match-update --------------|  When match data changes (via NOTIFY)
  |<---- gameclock-update ---------|  When game clock changes
  |<---- playclock-update ----------|  When play clock changes
  |<---- event-update -------------|  When football events change
  |                                   |
  |----- DISCONNECT ------------------->|  Client disconnects or closes connection
  |                                   |
```

#### Queue Management

Each client has:
- Individual queue per data type (match_data, playclock, gameclock, event)
- Match subscription mapping (match_id → list of client_ids)
- Automatic cleanup on disconnect

#### Timeout Configuration

- Queue get timeout: 12 hours (43200 seconds)
- If no messages received within timeout, connection closes gracefully

---

### WebSocket Endpoint 2: Match Statistics

Real-time match statistics with conflict resolution for collaborative editing.

#### Connection

```typescript
const ws = new WebSocket('ws://localhost:9000/api/matches/ws/matches/{match_id}/stats');
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID to get stats for |

**Note:** Client ID is auto-generated by server (`id(websocket)`) for this endpoint.

#### Authentication

**Current Status:** No authentication required

#### Initial Data

```typescript
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
  "server_timestamp": "2026-01-21T17:30:00.123456"
}
```

#### Client-Sent Messages

##### Update Stats

Client can send stat updates with timestamp for conflict resolution.

```typescript
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
  "timestamp": "2026-01-21T17:33:00.123456"
}
```

**Conflict Resolution:**
- Server compares client `timestamp` with last write timestamp
- If client timestamp is newer → update accepted and broadcast to all other clients
- If server timestamp is newer → update rejected, client receives `stats_sync` with current data

#### Server-Sent Messages

##### 1. Stats Update

Broadcast when any client updates stats (or server-side changes occur).

```typescript
{
  "type": "stats_update",
  "match_id": 123,
  "stats": {
    "match_id": 123,
    "team_a": { /* full stats structure */ },
    "team_b": { /* full stats structure */ }
  },
  "server_timestamp": "2026-01-21T17:31:00.123456"
}
```

##### 2. Stats Sync (Conflict Resolution)

Sent when client's update is rejected due to conflict (server has newer data).

```typescript
{
  "type": "stats_sync",
  "match_id": 123,
  "stats": {
    "match_id": 123,
    "team_a": { /* current server stats */ },
    "team_b": { /* current server stats */ }
  },
  "server_timestamp": "2026-01-21T17:32:00.123456"
}
```

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

#### Connection Lifecycle

```
Client                              Server
  |                                   |
  |----- CONNECT ---------------------->|
  |                                   |
  |<---- full_stats_update ------------|  Send complete match statistics
  |                                   |
  |----- stats_update (optional) ---->|
  |<---- stats_sync (if conflict) -----|  Server rejects client's update
  |                                   |
  |<---- stats_update (broadcast) -----|  Broadcast to all connected clients
  |                                   |
  |----- stats_update --------------->|
  |                                   |
  |<---- stats_update (broadcast) -----|
  |                                   |
  |----- DISCONNECT ------------------->|
  |                                   |
```

#### Client Pooling

- Multiple clients can connect to the same match
- Updates are broadcast to all clients (except sender for direct updates)
- Server tracks last write timestamp per match for conflict resolution

---

### WebSocket Connection Examples

#### Example 1: Connect to Match Data WebSocket

```typescript
function connectToMatchDataWebSocket(matchId: number, clientId: string) {
  const ws = new WebSocket(
    `ws://localhost:9000/api/matches/ws/id/${matchId}/${clientId}`
  );

  ws.onopen = () => {
    console.log('Connected to match data WebSocket');
  };

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
      case 'message-update':
      case 'match-update':
        console.log('Match data updated:', message);
        // Update match display, teams, scoreboard
        break;
        
      case 'gameclock-update':
        console.log('Game clock updated:', message.gameclock);
        // Update game clock display
        break;
        
      case 'playclock-update':
        console.log('Play clock updated:', message.playclock);
        // Update play clock display
        break;
        
      case 'event-update':
        console.log('Events updated:', message.events);
        // Update event log or timeline
        break;
        
      default:
        console.warn('Unknown message type:', message.type);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = (event) => {
    console.log('WebSocket connection closed:', event.code, event.reason);
    // Implement reconnection logic here
  };
}

// Usage
connectToMatchDataWebSocket(123, 'client-abc-123');
```

#### Example 2: Connect to Match Stats WebSocket

```typescript
function connectToMatchStatsWebSocket(matchId: number) {
  const ws = new WebSocket(
    `ws://localhost:9000/api/matches/ws/matches/${matchId}/stats`
  );

  ws.onopen = () => {
    console.log('Connected to match stats WebSocket');
  };

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
      case 'full_stats_update':
        console.log('Initial stats loaded:', message.stats);
        // Initialize stats display with full data
        break;
        
      case 'stats_update':
        console.log('Stats updated:', message.stats);
        // Update stats display with new values
        break;
        
      case 'stats_sync':
        console.log('Stats synced from server:', message.stats);
        // Your update was rejected, apply server data
        break;
        
      default:
        console.warn('Unknown message type:', message.type);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = (event) => {
    console.log('WebSocket connection closed:', event.code, event.reason);
    // Implement reconnection logic here
  };
}

// Usage
connectToMatchStatsWebSocket(123);
```

#### Example 3: Update Stats via WebSocket

```typescript
function updateStats(ws: WebSocket, matchId: number, newStats: any) {
  if (ws.readyState === WebSocket.OPEN) {
    const message = {
      type: 'stats_update',
      match_id: matchId,
      stats: newStats,
      timestamp: new Date().toISOString()
    };
    
    ws.send(JSON.stringify(message));
    console.log('Stats update sent');
  } else {
    console.error('WebSocket not connected');
  }
}

// Usage
const ws = new WebSocket('ws://localhost:9000/api/matches/ws/matches/123/stats');

// When stats change (e.g., user edits stats)
function onStatsChange(updatedStats) {
  updateStats(ws, 123, updatedStats);
}
```

#### Example 4: Reconnection Strategy

```typescript
class ReconnectingWebSocket {
  constructor(url: string, reconnectInterval = 5000) {
    this.url = url;
    this.reconnectInterval = reconnectInterval;
    this.ws = null;
    this.shouldReconnect = true;
    
    this.connect();
  }

  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.onMessage?.(message);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      
      if (this.shouldReconnect) {
        console.log(`Reconnecting in ${this.reconnectInterval}ms...`);
        setTimeout(() => this.connect(), this.reconnectInterval);
      }
    };
  }

  close() {
    this.shouldReconnect = false;
    this.ws?.close();
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket not connected');
    }
  }
}

// Usage
const matchWs = new ReconnectingWebSocket(
  'ws://localhost:9000/api/matches/ws/id/123/client-abc-123'
);

matchWs.onMessage = (message) => {
  console.log('Received:', message);
};
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

## WebSocket Troubleshooting Guide

### Common Issues and Solutions

#### 1. Connection Refused

**Symptoms:**
- WebSocket connection fails immediately
- Error: `WebSocket connection to 'ws://localhost:9000/...' failed`

**Causes:**
- Backend server not running
- Wrong URL or port
- Firewall blocking WebSocket connections

**Solutions:**
```bash
# Check if backend is running
curl http://localhost:9000/health

# Start backend if not running
python src/runserver.py

# Check firewall settings
# Ensure WebSocket connections are allowed on port 9000
```

#### 2. Connection Timeout

**Symptoms:**
- Connection attempt hangs
- Timeout after several seconds

**Causes:**
- Network latency
- Database connection issues
- PostgreSQL NOTIFY/LISTENER setup problems

**Solutions:**
- Check database connectivity
- Verify PostgreSQL triggers are configured
- Check backend logs for database errors

#### 3. Frequent Disconnections

**Symptoms:**
- WebSocket connects but disconnects randomly
- Error: `Connection closed by remote host`

**Causes:**
- Network instability
- Database connection drops
- WebSocket manager issues
- Client timeout (12-hour queue timeout)

**Solutions:**
- Implement exponential backoff reconnection strategy
- Check database connection stability
- Review server logs for errors
- Consider reducing queue timeout if needed

#### 4. No Messages Received

**Symptoms:**
- Connection established successfully
- No messages received from server
- Initial data messages not sent

**Causes:**
- PostgreSQL triggers not firing
- Match data doesn't exist
- Client not properly subscribed

**Solutions:**
```typescript
// Verify message handler is set up
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

// Check backend logs for NOTIFY messages
# Check PostgreSQL triggers
SELECT * FROM pg_trigger WHERE tgname LIKE '%websocket%';
```

#### 5. Message Parse Errors

**Symptoms:**
- `JSON.parse` errors
- Messages with unexpected structure
- Malformed data

**Causes:**
- Non-JSON messages
- Invalid message format
- Schema mismatches

**Solutions:**
```typescript
// Add error handling for JSON parsing
ws.onmessage = (event) => {
  try {
    const message = JSON.parse(event.data);
    handleMessage(message);
  } catch (error) {
    console.error('Failed to parse message:', event.data, error);
  }
};

// Validate message structure
function handleMessage(message: any) {
  if (!message.type || !message.match_id) {
    console.warn('Invalid message structure:', message);
    return;
  }
  // Process message
}
```

#### 6. Conflict Resolution Loops

**Symptoms:**
- Continuous `stats_sync` messages
- Stats never successfully update
- Infinite loop of updates

**Causes:**
- Multiple clients updating simultaneously
- Timestamp synchronization issues
- Incorrect timestamp handling

**Solutions:**
```typescript
// Implement debouncing for updates
let updatePending = false;

function sendStatsUpdate(stats: any) {
  if (updatePending) {
    console.log('Update already pending, skipping');
    return;
  }
  
  updatePending = true;
  ws.send(JSON.stringify({
    type: 'stats_update',
    match_id: matchId,
    stats: stats,
    timestamp: new Date().toISOString()
  }));
  
  // Reset after delay
  setTimeout(() => { updatePending = false; }, 1000);
}

// Handle stats_sync to update local state
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'stats_sync') {
    console.log('Applying server state:', message.stats);
    // Update local state with server data
    updatePending = false;
  }
};
```

### Debugging Tips

#### Enable WebSocket Debugging

```typescript
// Enable verbose logging
const ws = new WebSocket('ws://localhost:9000/api/matches/ws/id/123/client-abc');

ws.onopen = () => {
  console.log('[WebSocket] Connected');
};

ws.onmessage = (event) => {
  console.log('[WebSocket] Message:', event.data);
};

ws.onerror = (error) => {
  console.error('[WebSocket] Error:', error);
};

ws.onclose = (event) => {
  console.log('[WebSocket] Closed:', event.code, event.reason, event.wasClean);
};
```

#### Check Backend Logs

```bash
# WebSocket connection logs
tail -f logs/backend.log | grep WebSocket

# Match data handler logs
tail -f logs/backend.log | grep MatchDataWebSocket

# Stats handler logs
tail -f logs/backend.log | grep MatchStatsWebSocket

# Check for errors
tail -f logs/backend.log | grep -i error
```

#### Verify PostgreSQL Notifications

```sql
-- Check if NOTIFY messages are being sent
SELECT pg_notification_queue_usage();

-- Check active listeners
SELECT * FROM pg_listening_channels();

-- Manually trigger a notification for testing
NOTIFY matchdata_change, '{"match_id": 123}';
```

#### Monitor WebSocket Connections

```typescript
// Track connection state
class WebSocketMonitor {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private lastMessageTime = Date.now();

  connect(url: string) {
    this.ws = new WebSocket(url);
    
    this.ws.onopen = () => {
      console.log('[Monitor] Connected, attempts:', this.reconnectAttempts);
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      this.lastMessageTime = Date.now();
      const timeSinceLastMessage = Date.now() - this.lastMessageTime;
      
      if (timeSinceLastMessage > 60000) {  // 1 minute
        console.warn('[Monitor] No messages for 1 minute');
      }
    };

    this.ws.onerror = (error) => {
      console.error('[Monitor] Error, attempts:', this.reconnectAttempts);
      this.reconnectAttempts++;
    };

    this.ws.onclose = (event) => {
      console.log('[Monitor] Closed, code:', event.code);
      if (event.code !== 1000) {
        // Abnormal close, attempt reconnect
        this.reconnectAttempts++;
        setTimeout(() => this.connect(url), Math.min(1000 * this.reconnectAttempts, 30000));
      }
    };
  }
}
```

### Performance Optimization

#### 1. Batch Updates

```typescript
// Collect multiple updates before sending
const updateQueue: any[] = [];
let flushScheduled = false;

function queueUpdate(update: any) {
  updateQueue.push(update);
  
  if (!flushScheduled) {
    flushScheduled = true;
    requestAnimationFrame(flushUpdates);
  }
}

function flushUpdates() {
  if (updateQueue.length === 0) {
    flushScheduled = false;
    return;
  }
  
  // Apply all updates at once
  applyUpdates(updateQueue);
  updateQueue.length = 0;
  flushScheduled = false;
}
```

#### 2. Use Server-Sent Caching

```typescript
// Cache initial data to avoid redundant requests
let cachedStats: any = null;

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'full_stats_update') {
    cachedStats = message.stats;
    updateDisplay(message.stats);
  } else if (message.type === 'stats_update') {
    if (cachedStats) {
      // Merge update with cached data
      const merged = mergeStats(cachedStats, message.stats);
      cachedStats = merged;
      updateDisplay(merged);
    }
  }
};
```

#### 3. Debounce Updates

```typescript
// Debounce rapid updates to prevent UI thrashing
let debounceTimer: any = null;

function debouncedUpdate(update: any) {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    applyUpdate(update);
  }, 100);  // 100ms debounce
}
```

### Testing WebSocket Connections

#### Test Match Data WebSocket

```javascript
// Simple test script
const testWs = new WebSocket('ws://localhost:9000/api/matches/ws/id/123/test-client');

let messageCount = 0;
let startTime = Date.now();

testWs.onopen = () => {
  console.log('✅ WebSocket connected');
};

testWs.onmessage = (event) => {
  messageCount++;
  const elapsed = (Date.now() - startTime) / 1000;
  console.log(`📨 Message #${messageCount} (${elapsed.toFixed(2)}s)`);
  console.log('Data:', JSON.parse(event.data));
};

testWs.onerror = (error) => {
  console.error('❌ WebSocket error:', error);
};

testWs.onclose = (event) => {
  console.log(`🔌 WebSocket closed after ${(Date.now() - startTime) / 1000}s`);
  console.log('Messages received:', messageCount);
};

// Auto-close after 30 seconds
setTimeout(() => {
  testWs.close();
}, 30000);
```

#### Test Match Stats WebSocket

```javascript
const testStatsWs = new WebSocket('ws://localhost:9000/api/matches/ws/matches/123/stats');

testStatsWs.onopen = () => {
  console.log('✅ Stats WebSocket connected');
};

testStatsWs.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('📊 Message type:', message.type);
  
  if (message.type === 'full_stats_update') {
    console.log('📦 Full stats loaded');
  } else if (message.type === 'stats_update') {
    console.log('🔄 Stats updated');
  } else if (message.type === 'stats_sync') {
    console.log('🔒 Stats synced (conflict)');
  }
};

testStatsWs.onerror = (error) => {
  console.error('❌ Stats WebSocket error:', error);
};

testStatsWs.onclose = (event) => {
  console.log('🔌 Stats WebSocket closed');
};
```

### Security Considerations

#### Current Status

WebSocket endpoints currently **do not require authentication**. This is acceptable for:

- Public match data viewing
- Real-time scoreboards
- Public statistics

#### Future Authentication

When authentication is implemented, use:

```typescript
// Option 1: Query parameter (recommended)
const token = getAuthToken();
const ws = new WebSocket(
  `ws://localhost:9000/api/matches/ws/id/123/client-abc?token=${token}`
);

// Option 2: Subprotocol
const ws = new WebSocket('ws://localhost:9000/api/matches/ws/id/123/client-abc', ['statsboard-auth']);
```

#### Data Validation

Always validate WebSocket messages on client side:

```typescript
function validateMessage(message: any): boolean {
  // Check required fields
  if (!message || typeof message !== 'object') {
    return false;
  }
  
  if (!message.type || typeof message.type !== 'string') {
    return false;
  }
  
  if (!message.match_id || typeof message.match_id !== 'number') {
    return false;
  }
  
  // Type-specific validation
  switch (message.type) {
    case 'gameclock-update':
      return !!message.gameclock && typeof message.gameclock.gameclock === 'number';
      
    case 'playclock-update':
      return !!message.playclock && typeof message.playclock.playclock === 'number';
      
    case 'stats_update':
      return !!message.stats && !!message.timestamp;
      
    default:
      return true;
  }
}

ws.onmessage = (event) => {
  try {
    const message = JSON.parse(event.data);
    
    if (!validateMessage(message)) {
      console.warn('Invalid message received:', message);
      return;
    }
    
    handleMessage(message);
  } catch (error) {
    console.error('Message validation error:', error);
  }
};
```

### Best Practices

1. **Always handle connection states:** Monitor `onopen`, `onmessage`, `onerror`, `onclose`
2. **Implement exponential backoff:** Don't spam reconnection attempts
3. **Validate messages:** Never trust WebSocket data without validation
4. **Cache data:** Store initial data and apply incremental updates
5. **Debounce updates:** Prevent UI thrashing from rapid updates
6. **Log everything:** Enable verbose logging for debugging
7. **Test with curl:** Verify server is running before connecting
8. **Monitor performance:** Track message frequency and connection stability
9. **Handle errors gracefully:** Show user-friendly error messages
10. **Clean up on disconnect:** Remove event listeners and timers

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
  team_id: number;
  match_id: number;
  player_team_tournament_id: number;
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
| `team_id` | number | Team ID for the player match | integer |
| `match_id` | number | Match ID for the player match | integer |
| `player_team_tournament_id` | number | PlayerTeamTournament record ID | integer |
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

## Sports API

Manage sports categories and their associated data (teams, players, positions, tournaments). Sports are the top-level categorization for all athletic activities in the system.

### Response Schemas

```typescript
interface SportSchema {
  id: number;
  title: string; // Max 255 characters
  description: string | null;
}

interface SportSchemaCreate {
  title: string; // Max 255 characters
  description: string | null; // Optional
}

interface SportSchemaUpdate {
  title: string | null; // Optional - Max 255 characters
  description: string | null; // Optional
}
```

---

### POST /api/sports/

Create a new sport.

**Endpoint:**
```
POST /api/sports/
```

**Request Body:**
```json
{
  "title": "American Football",
  "description": "American football rules and gameplay"
}
```

**Request Schema:**
```typescript
interface SportSchemaCreate {
  title: string; // Max 255 characters
  description: string | null; // Optional description
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "American Football",
  "description": "American football rules and gameplay"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Bad request - validation error |
| 409 | Conflict - sport with this title already exists |
| 500 | Internal server error |

---

### PUT /api/sports/{item_id}/

Update a sport by ID.

**Endpoint:**
```
PUT /api/sports/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Sport ID to update |

**Request Body:**
```json
{
  "title": "American Football",
  "description": "Updated description"
}
```

**Request Schema:**
```typescript
interface SportSchemaUpdate {
  title: string | null; // Optional - Max 255 characters
  description: string | null; // Optional
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "American Football",
  "description": "Updated description"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Sport not found |
| 500 | Internal server error |

---

### GET /api/sports/id/{item_id}/

Get a sport by ID.

**Endpoint:**
```
GET /api/sports/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Sport ID to retrieve |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "title": "American Football",
    "description": "American football rules and gameplay"
  },
  "status_code": 200,
  "success": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Sport not found |
| 500 | Internal server error |

---

### GET /api/sports/

Get all sports without pagination. Returns a simple list.

**Endpoint:**
```
GET /api/sports/
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "American Football",
    "description": "American football rules"
  },
  {
    "id": 2,
    "title": "Basketball",
    "description": "Basketball rules"
  }
]
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

### GET /api/sports/paginated

Search sports by title with pagination, sorting, and filtering.

**Endpoint:**
```
GET /api/sports/paginated
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (1-based) |
| `items_per_page` | integer | No | 20 | Items per page (max 100) |
| `order_by` | string | No | "title" | First sort column |
| `order_by_two` | string | No | "id" | Second sort column |
| `ascending` | boolean | No | true | Sort order (true=asc, false=desc) |
| `search` | string | No | - | Search query for title (case-insensitive) |

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "title": "American Football",
      "description": "American football rules"
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
- Search is case-insensitive and uses partial matching on `title` field
- Uses ICU collation for consistent international character handling
- Defaults to ordering by `title` ascending, then by `id`

**Error Responses:**

| Status | Description |
|--------|-------------|
| 422 | Validation error - invalid query parameters |
| 500 | Internal server error |

---

### GET /api/sports/id/{sport_id}/tournaments

Get all tournaments for a specific sport.

**Endpoint:**
```
GET /api/sports/id/{sport_id}/tournaments
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sport_id` | integer | Yes | Sport ID |

**Response (200 OK):**
```json
[
  {
    "id": 5,
    "title": "Super Bowl 2024",
    "season_id": 2,
    "sport_id": 1
  },
  {
    "id": 6,
    "title": "NFL Regular Season 2024",
    "season_id": 2,
    "sport_id": 1
  }
]
```

**Behavior:**
- Returns all tournaments belonging to the specified sport
- Ordered by tournament title in ascending order
- Returns empty array if no tournaments found

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

### GET /api/sports/id/{sport_id}/teams

Get all teams for a specific sport.

**Endpoint:**
```
GET /api/sports/id/{sport_id}/teams
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sport_id` | integer | Yes | Sport ID |

**Response (200 OK):**
```json
[
  {
    "id": 10,
    "title": "Patriots",
    "sport_id": 1
  },
  {
    "id": 11,
    "title": "Chiefs",
    "sport_id": 1
  }
]
```

**Behavior:**
- Returns all teams belonging to the specified sport
- Returns empty array if no teams found

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

### GET /api/sports/id/{sport_id}/players

Get all players for a specific sport.

**Endpoint:**
```
GET /api/sports/id/{sport_id}/players
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sport_id` | integer | Yes | Sport ID |

**Response (200 OK):**
```json
[
  {
    "id": 100,
    "first_name": "Tom",
    "second_name": "Brady",
    "sport_id": 1
  },
  {
    "id": 101,
    "first_name": "Patrick",
    "second_name": "Mahomes",
    "sport_id": 1
  }
]
```

**Behavior:**
- Returns all players associated with the specified sport
- Returns empty array if no players found

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

### GET /api/sports/id/{sport_id}/positions

Get all positions for a specific sport.

**Endpoint:**
```
GET /api/sports/id/{sport_id}/positions
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sport_id` | integer | Yes | Sport ID |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Quarterback",
    "sport_id": 1
  },
  {
    "id": 2,
    "title": "Wide Receiver",
    "sport_id": 1
  }
]
```

**Behavior:**
- Returns all positions belonging to the specified sport
- Returns empty array if no positions found

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

### GET /api/sports/id/{sport_id}/teams/paginated

Get teams for a specific sport with pagination, sorting, and search.

**Endpoint:**
```
GET /api/sports/id/{sport_id}/teams/paginated
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sport_id` | integer | Yes | Sport ID |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (1-based) |
| `items_per_page` | integer | No | 20 | Items per page (max 100) |
| `order_by` | string | No | "title" | First sort column |
| `order_by_two` | string | No | "id" | Second sort column |
| `ascending` | boolean | No | true | Sort order (true=asc, false=desc) |
| `search` | string | No | - | Search query for team title (case-insensitive) |

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 10,
      "title": "Patriots",
      "sport_id": 1
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
- Search is case-insensitive and uses partial matching on `title` field
- Filters teams by the specified sport_id
- Uses ICU collation for consistent international character handling

**Error Responses:**

| Status | Description |
|--------|-------------|
| 422 | Validation error - invalid query parameters |
| 500 | Internal server error |

---

### DELETE /api/sports/id/{model_id}

Delete a sport by ID. Requires admin role.

**Endpoint:**
```
DELETE /api/sports/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | Sport ID to delete |

**Response (200 OK):**
```json
{
  "detail": "Sport 1 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | Sport not found |
| 500 | Internal server error |

---

## Positions API

Manage player positions within sports. Positions define the roles players can take during gameplay (e.g., Quarterback, Wide Receiver in football).

### Response Schemas

```typescript
interface PositionSchema {
  id: number;
  title: string; // Max 30 characters
  sport_id: number; // Reference to sport
}

interface PositionSchemaCreate {
  title: string; // Max 30 characters
  sport_id: number; // Required - Reference to sport
}

interface PositionSchemaUpdate {
  title: string | null; // Optional - Max 30 characters
  sport_id: number | null; // Optional
}
```

---

### POST /api/positions/

Create a new position.

**Endpoint:**
```
POST /api/positions/
```

**Request Body:**
```json
{
  "title": "Quarterback",
  "sport_id": 1
}
```

**Request Schema:**
```typescript
interface PositionSchemaCreate {
  title: string; // Max 30 characters, defaults to "Position"
  sport_id: number; // Required - ID of the sport this position belongs to
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Quarterback",
  "sport_id": 1
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Bad request - validation error |
| 409 | Conflict - position creation failed |
| 500 | Internal server error |

---

### PUT /api/positions/{item_id}/

Update a position by ID.

**Endpoint:**
```
PUT /api/positions/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Position ID to update |

**Request Body:**
```json
{
  "title": "Wide Receiver",
  "sport_id": 1
}
```

**Request Schema:**
```typescript
interface PositionSchemaUpdate {
  title: string | null; // Optional - Max 30 characters
  sport_id: number | null; // Optional
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Wide Receiver",
  "sport_id": 1
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Position not found |
| 500 | Internal server error |

---

### GET /api/positions/title/{item_title}/

Get a position by title.

**Endpoint:**
```
GET /api/positions/title/{item_title}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_title` | string | Yes | Position title to search |

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Quarterback",
  "sport_id": 1
}
```

**Behavior:**
- Case-sensitive exact match on position title
- Returns 404 if position not found

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Position not found |
| 500 | Internal server error |

---

### DELETE /api/positions/id/{model_id}

Delete a position by ID. Requires admin role.

**Endpoint:**
```
DELETE /api/positions/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | Position ID to delete |

**Response (200 OK):**
```json
{
  "detail": "Position 1 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | Position not found |
| 500 | Internal server error |

---

## Scoreboards API

Manage scoreboard display settings for matches. Scoreboards control what elements are shown during game broadcasts (quarters, time, play clock, down/distance, logos, sponsors, etc.).

### Response Schemas

```typescript
interface ScoreboardSchema {
  id: number;
  is_qtr: boolean; // Show quarter display
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

  match_id: number | null; // Associated match ID
}
```

---

### POST /api/scoreboards/

Create a new scoreboard configuration.

**Endpoint:**
```
POST /api/scoreboards/
```

**Request Body:**
```json
{
  "is_qtr": true,
  "is_time": true,
  "is_playclock": true,
  "is_downdistance": true,
  "is_tournament_logo": true,
  "is_main_sponsor": true,
  "is_sponsor_line": true,
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
  "is_time": true,
  "is_playclock": true,
  "is_downdistance": true,
  "is_tournament_logo": true,
  "is_main_sponsor": true,
  "is_sponsor_line": true,
  "is_match_sponsor_line": false,
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

## Playclocks API

Manage play clocks for matches. The play clock counts down the time between plays in American football.

### Response Schemas

```typescript
interface PlayClockSchema {
  id: number;
  playclock: number | null; // Current time in seconds (max 10000)
  playclock_status: string; // Status: "stopped", "running", "paused" (max 50 chars)
  match_id: number | null; // Associated match ID
  version: number; // Version number, starts at 1, increments on each update
}

interface PlayClockSchemaCreate {
  playclock: number | null; // Optional time in seconds (max 10000)
  playclock_status: string; // Status, defaults to "stopped" (max 50 chars)
  match_id: number | null; // Optional match ID
  version?: number; // Version number, defaults to 1
}

interface PlayClockSchemaUpdate {
  playclock: number | null; // Optional time in seconds
  playclock_status: string | null; // Optional status
  match_id: number | null; // Optional match ID
}
```

---

### POST /api/playclock/

Create a new play clock.

**Endpoint:**
```
POST /api/playclock/
```

**Request Body:**
```json
{
  "playclock": 40,
  "playclock_status": "stopped",
  "match_id": 123
}
```

**Request Schema:**
```typescript
interface PlayClockSchemaCreate {
  playclock: number | null; // Optional time in seconds (max 10000)
  playclock_status: string; // Status, defaults to "stopped" (max 50 chars)
  match_id: number | null; // Optional associated match ID
  version?: number; // Version number, defaults to 1
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "playclock": 40,
  "playclock_status": "stopped",
  "match_id": 123,
  "version": 1
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Bad request - validation error |
| 500 | Internal server error - database error |

---

### PUT /api/playclock/{item_id}/

Update a play clock by ID.

**Endpoint:**
```
PUT /api/playclock/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | PlayClock ID to update |

**Request Body:**
```json
{
  "playclock": 35,
  "playclock_status": "running"
}
```

**Request Schema:**
```typescript
interface PlayClockSchemaUpdate {
  playclock: number | null; // Optional time in seconds
  playclock_status: string | null; // Optional status
  match_id: number | null; // Optional match ID
  version?: number; // Optional version number (auto-incremented on update)
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "playclock": 35,
  "playclock_status": "running",
  "match_id": 123,
  "version": 2
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Playclock not found |
| 500 | Internal server error |

---

### PUT /api/playclock/id/{item_id}/

Update a play clock by ID with JSONResponse format.

**Endpoint:**
```
PUT /api/playclock/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | PlayClock ID to update |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "playclock": 35,
    "playclock_status": "running",
    "match_id": 123,
    "version": 2
  },
  "status_code": 200,
  "success": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Playclock not found |
| 500 | Internal server error |

---

### GET /api/playclock/id/{item_id}/

Get a play clock by ID.

**Endpoint:**
```
GET /api/playclock/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | PlayClock ID to retrieve |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "title": "Playclock",
    "description": "Match playclock"
  },
  "status_code": 200,
  "success": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Playclock not found |
| 500 | Internal server error |

---

### PUT /api/playclock/id/{item_id}/running/{sec}/

Start the play clock and begin countdown.

**Endpoint:**
```
PUT /api/playclock/id/{item_id}/running/{sec}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | PlayClock ID |
| `sec` | integer | Yes | Starting time in seconds |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "playclock": 40,
    "playclock_status": "running",
    "match_id": 123,
    "version": 2
  },
  "status_code": 200,
  "success": true
}
```

**Behavior:**
- Enables match data clock queues for SSE
- If playclock was not already running, updates to specified time and status "running"
- Starts background task for decrementing the clock if background tasks are enabled
- Background task decrements playclock every second until stopped

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Playclock not found |
| 500 | Internal server error - database error |

---

### PUT /api/playclock/id/{item_id}/{item_status}/{sec}/

Reset the play clock to a specific time and status.

**Endpoint:**
```
PUT /api/playclock/id/{item_id}/{item_status}/{sec}/
```

**Path Parameters:**

| Parameter | Type | Required | Description | Examples |
|-----------|------|----------|-------------|------------|
| `item_id` | integer | Yes | PlayClock ID | - |
| `item_status` | string | Yes | New status | "stopped", "running", "paused" |
| `sec` | integer | Yes | Time in seconds | 25, 40, 25 |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "playclock": 25,
    "playclock_status": "stopped",
    "match_id": 123
  },
  "status_code": 200,
  "success": true
}
```

**Behavior:**
- Updates playclock to specified time and status
- Commonly used to reset to 40 seconds (stopped) for new play

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Playclock not found |
| 500 | Internal server error - database error |

---

### PUT /api/playclock/id/{item_id}/stopped/

Stop the play clock and clear time.

**Endpoint:**
```
PUT /api/playclock/id/{item_id}/stopped/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | PlayClock ID |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "playclock": null,
    "playclock_status": "stopped",
    "match_id": 123
  },
  "status_code": 200,
  "success": true
}
```

**Behavior:**
- Sets playclock to `null` and status to "stopped"
- Used to clear clock display between plays

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Playclock not found |
| 500 | Internal server error - database error |

---

### DELETE /api/playclock/id/{model_id}

Delete a play clock by ID. Requires admin role.

**Endpoint:**
```
DELETE /api/playclock/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | PlayClock ID to delete |

**Response (200 OK):**
```json
{
  "detail": "Playclock 1 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | Playclock not found |
| 500 | Internal server error |

---

## Gameclocks API

Manage game clocks for matches. The game clock counts down the total game time for quarters and halves in American football.

### Response Schemas

```typescript
interface GameClockSchema {
  id: number;
  gameclock: number; // Total time in seconds (max 10000), default 720 (12 minutes)
  gameclock_max: number | null; // Maximum time in seconds, default 720
  gameclock_status: string; // Status: "stopped", "running", "paused" (max 50 chars)
  gameclock_time_remaining: number | null; // Remaining time during countdown
  match_id: number | null; // Associated match ID
  version: number; // Version number, starts at 1, increments on each update
}

interface GameClockSchemaCreate {
  gameclock: number; // Total time in seconds (max 10000), default 720
  gameclock_max: number | null; // Optional max time
  gameclock_status: string; // Status, defaults to "stopped" (max 50 chars)
  gameclock_time_remaining: number | null; // Optional remaining time
  match_id: number | null; // Optional match ID
  version?: number; // Version number, defaults to 1
}

interface GameClockSchemaUpdate {
  gameclock: number | null; // Optional time in seconds
  gameclock_max: number | null; // Optional max time
  gameclock_status: string | null; // Optional status
  gameclock_time_remaining: number | null; // Optional remaining time
  match_id: number | null; // Optional match ID
}
```

---

### POST /api/gameclock/

Create a new game clock.

**Endpoint:**
```
POST /api/gameclock/
```

**Request Body:**
```json
{
  "gameclock": 720,
  "gameclock_max": 720,
  "gameclock_status": "stopped",
  "match_id": 123
}
```

**Request Schema:**
```typescript
interface GameClockSchemaCreate {
  gameclock: number; // Total time in seconds (max 10000), default 720
  gameclock_max: number | null; // Optional maximum time
  gameclock_status: string; // Status, defaults to "stopped" (max 50 chars)
  gameclock_time_remaining: number | null; // Optional remaining time
  match_id: number | null; // Optional associated match ID
  version?: number; // Version number, defaults to 1
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "gameclock": 720,
  "gameclock_max": 720,
  "gameclock_status": "stopped",
  "gameclock_time_remaining": null,
  "match_id": 123,
  "version": 1
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Bad request - validation error |
| 500 | Internal server error |

---

### PUT /api/gameclock/{item_id}/

Update a game clock by ID.

**Endpoint:**
```
PUT /api/gameclock/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | GameClock ID to update |

**Request Body:**
```json
{
  "gameclock_status": "running"
}
```

**Request Schema:**
```typescript
interface GameClockSchemaUpdate {
  gameclock: number | null; // Optional time in seconds
  gameclock_max: number | null; // Optional max time
  gameclock_status: string | null; // Optional status
  gameclock_time_remaining: number | null; // Optional remaining time
  match_id: number | null; // Optional match ID
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "gameclock": 720,
  "gameclock_max": 720,
  "gameclock_status": "running",
  "gameclock_time_remaining": 720,
  "match_id": 123,
  "version": 2
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Gameclock not found |
| 409 | Error updating gameclock |
| 500 | Internal server error |

---

### PUT /api/gameclock/id/{item_id}/

Update a game clock by ID with JSONResponse format.

**Endpoint:**
```
PUT /api/gameclock/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | GameClock ID to update |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "gameclock": 720,
    "gameclock_status": "running",
    "gameclock_time_remaining": 720,
    "match_id": 123,
    "version": 2
  },
  "status_code": 200,
  "success": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Gameclock not found |
| 500 | Internal server error |

---

### PUT /api/gameclock/id/{gameclock_id}/running/

Start the game clock and begin countdown.

**Endpoint:**
```
PUT /api/gameclock/id/{gameclock_id}/running/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `gameclock_id` | integer | Yes | GameClock ID |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "gameclock": 720,
    "gameclock_max": 720,
    "gameclock_status": "running",
    "gameclock_time_remaining": 720,
    "match_id": 123
  },
  "status_code": 200,
  "success": true
}
```

**Behavior:**
- If gameclock was not running, updates status to "running" and sets `gameclock_time_remaining` to current `gameclock` value
- Starts background task for decrementing the game clock
- Background task decrements `gameclock_time_remaining` every second
- If gameclock was already running, returns current state with message

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

### PUT /api/gameclock/id/{item_id}/paused/

Pause the game clock.

**Endpoint:**
```
PUT /api/gameclock/id/{item_id}/paused/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | GameClock ID |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "gameclock": 720,
    "gameclock_status": "paused",
    "gameclock_time_remaining": 650,
    "match_id": 123
  },
  "status_code": 200,
  "success": true
}
```

**Behavior:**
- Pauses the countdown timer
- Keeps `gameclock_time_remaining` at current value

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

### PUT /api/gameclock/id/{item_id}/{item_status}/{sec}/

Reset the game clock to a specific time and status.

**Endpoint:**
```
PUT /api/gameclock/id/{item_id}/{item_status}/{sec}/
```

**Path Parameters:**

| Parameter | Type | Required | Description | Examples |
|-----------|------|----------|-------------|------------|
| `item_id` | integer | Yes | GameClock ID | - |
| `item_status` | string | Yes | New status | "stopped", "running", "paused" |
| `sec` | integer | Yes | Time in seconds | 720, 900, 1800 |

**Response (200 OK):**
```json
{
  "content": {
    "id": 1,
    "gameclock": 900,
    "gameclock_max": 720,
    "gameclock_status": "stopped",
    "gameclock_time_remaining": null,
    "match_id": 123
  },
  "status_code": 200,
  "success": true
}
```

**Behavior:**
- Updates gameclock to specified time and status
- Commonly used to reset quarter/half times (900s = 15 min, 1800s = 30 min)

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

### DELETE /api/gameclock/id/{model_id}

Delete a game clock by ID. Requires admin role.

**Endpoint:**
```
DELETE /api/gameclock/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | GameClock ID to delete |

**Response (200 OK):**
```json
{
  "detail": "Gameclock 1 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | Gameclock not found |
| 500 | Internal server error |

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

### GET /api/matches/id/{match_id}/comprehensive/

Get all match data including match info, match data, teams, players with person data, events, and scoreboard. This is the maximum data endpoint for scoreboard control.

**Endpoint:**
```
GET /api/matches/id/{match_id}/comprehensive/
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
    "match_date": "2025-01-03T10:00:00",
    "week": 1,
    "isprivate": false
  },
  "match_data": {
    "id": 1,
    "match_id": 123,
    "score_team_a": 14,
    "score_team_b": 10,
    "game_status": "in-progress",
    "qtr": "3rd",
    "ball_on": 35,
    "down": "2nd",
    "distance": "7",
    "timeout_team_a": "●●",
    "timeout_team_b": "●●●",
    "field_length": 92
  },
  "teams": {
    "team_a": {
      "id": 1,
      "title": "Team A",
      "city": "City A",
      "team_color": "#ff0000",
      "team_logo_url": "https://...",
      "team_logo_icon_url": "https://...",
      "team_logo_web_url": "https://..."
    },
    "team_b": {
      "id": 2,
      "title": "Team B",
      "city": "City B",
      "team_color": "#0000ff",
      "team_logo_url": "https://...",
      "team_logo_icon_url": "https://...",
      "team_logo_web_url": "https://..."
    }
  },
  "players": [
    {
      "id": 456,
      "team_id": 1,
      "match_id": 123,
      "player_team_tournament_id": 789,
      "player_id": 789,
      "player": {
        "id": 789,
        "player_eesl_id": 12345,
        "person_id": 123
      },
      "team": {
        "id": 1,
        "title": "Team A",
        "team_color": "#FF0000"
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
        "person_photo_url": "https://..."
      },
      "is_starting": true,
      "starting_type": "offense"
    }
  ],
  "events": [
    {
      "id": 1,
      "match_id": 123,
      "event_number": 1,
      "event_qtr": 1,
      "ball_on": 20,
      "play_type": "pass",
      "play_result": "complete",
      "score_result": "touchdown",
      "event_qb": 456,
      "pass_received_player": 457,
      "run_player": null,
      "kick_player": null,
      "offense_team": 1
    }
  ],
  "scoreboard": {
    "id": 1,
    "match_id": 123,
    "is_qtr": true,
    "is_time": true,
    "is_playclock": true,
    "is_downdistance": true,
    "is_tournament_logo": true,
    "is_main_sponsor": true,
    "is_sponsor_line": true,
    "team_a_game_color": "#ff0000",
    "team_b_game_color": "#0000ff",
    "team_a_game_title": "Team A",
    "team_b_game_title": "Team B",
    "scale_tournament_logo": 2.0,
    "scale_main_sponsor": 2.0,
    "scale_logo_a": 2.0,
    "scale_logo_b": 2.0,
    "is_flag": false,
    "is_goal_team_a": false,
    "is_goal_team_b": false,
    "is_timeout_team_a": false,
    "is_timeout_team_b": false
  }
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Match not found |
| 500 | Internal server error |

**Use Cases:**
- Scoreboard control interface needs all match data
- Real-time statistics display
- Match replay systems
- Analytics and reporting

**Notes:**
- This endpoint provides the maximum amount of match data in a single request
- Uses optimized loading strategies (selectinload) for performance
- All data fetched in minimal number of queries

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
