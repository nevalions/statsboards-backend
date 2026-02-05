# User API

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
