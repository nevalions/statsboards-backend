# Positions API

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
