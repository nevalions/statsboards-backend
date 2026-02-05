# Sponsor-Sponsor Line Connection API

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
