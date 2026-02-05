# Sports API

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
