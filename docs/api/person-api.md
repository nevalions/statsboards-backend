# Person API

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
