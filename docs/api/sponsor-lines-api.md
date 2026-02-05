# Sponsor Lines API

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

### GET /api/sponsor_lines/paginated

Search sponsor lines with pagination and sorting.

**Endpoint:**
```
GET /api/sponsor_lines/paginated
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
      "title": "Premier Sponsors",
      "is_visible": true
    },
    {
      "id": 2,
      "title": "Secondary Sponsors",
      "is_visible": false
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
interface PaginatedSponsorLineResponse {
  data: SponsorLineSchema[];
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
- Empty `search` parameter returns all sponsor lines
- Default sorting: by `title` ascending, then by `id`

**Examples:**

1. **Get all sponsor lines with pagination:**
```
GET /api/sponsor_lines/paginated?page=1&items_per_page=20
```

2. **Search sponsor lines by title:**
```
GET /api/sponsor_lines/paginated?search=Premier&page=1&items_per_page=20
```

3. **Custom ordering:**
```
GET /api/sponsor_lines/paginated?order_by=title&order_by_two=id&ascending=false
```

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
