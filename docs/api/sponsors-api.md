# Sponsors API

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

### GET /api/sponsors/

Get all sponsors.

**Endpoint:**
```
GET /api/sponsors/
```

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

**Response Schema:**
```typescript
type GetSponsorsResponse = SponsorSchema[];
```

**Error Responses:**

| Status | Description |
|--------|-------------|
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

**Behavior Notes:**
- The deletion will automatically clean up references to the sponsor in:
  - Tournament records (clears main_sponsor_id)
  - Team records (clears main_sponsor_id)
  - Match records (clears main_sponsor_id)
  - Sponsor line associations (deletes SponsorSponsorLineDB entries)


**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - requires admin role |
| 500 | Internal Server Error - server error |

---
