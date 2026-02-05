# Role API

Manage system roles for user authorization. Roles control what users can access and do within the application.

### GET /api/roles/

List all roles (unpaginated).

**Endpoint:**
```
GET /api/roles/
```

**Response (200 OK):**
```json
[
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
]
```

**Response Schema:**
```typescript
interface Role {
  id: number;
  name: string;
  description: string | null;
  user_count: number;
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
