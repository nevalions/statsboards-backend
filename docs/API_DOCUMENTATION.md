# Backend API Documentation

Frontend integration guide for StatsBoards Backend APIs and WebSocket endpoints.

## Table of Contents

  - [API Routing Conventions](#api-routing-conventions)
  - [Privacy and User Ownership Filtering](#privacy-and-user-ownership-filtering)
  - [Role API](#role-api)
  - [User API](#user-api)
  - [Person API](#person-api)
 - [Player Search API](#player-search-api)
  - [Player Sport Management API](#player-sport-management-api)
  - [Player Career API](#player-career-api)
  - [Player Detail Context API](#player-detail-context-api)
- [Teams in Tournament API](#teams-in-tournament-api)
- [Available Teams for Tournament API](#available-teams-for-tournament-api)
- [Available Players for Tournament API](#available-players-for-tournament-api)
- [Players in Tournament API](#get-apitournamentsidtournament_idplayerspaginated)
- [Players Without Team in Tournament API](#players-without-team-in-tournament-api)
- [Available Players for Team in Match API](#available-players-for-team-in-match-api)
- [Match Stats API](#match-stats-api)
- [WebSocket Message Formats](#websocket-message-formats)
- [Player Match API](#player-match-api)
- [Team Rosters API](#team-rosters-api)
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
| **Delete** | `DELETE /{resource}/{item_id}/` | `DELETE /api/teams/5/` | Delete resource by ID |

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
DELETE /api/teams/5/
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

### DELETE /api/roles/{item_id}/

Delete a role. Requires admin role.

**Endpoint:**
```
DELETE /api/roles/{item_id}/
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Role ID |

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
| 404 | Role not found |
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 500 | Internal server error |

**Behavior:**
- Cannot delete roles that have users assigned to them
- Users must be removed from the role first (via user role assignment endpoints)
- Prevents accidental deletion of roles in use

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
  "roles": ["user"]
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
  "email": "newemail@example.com",
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
  "email": "admin@example.com",
  "is_active": false,
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
  "roles": ["user", "admin"]
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
  "roles": ["user"]
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

Search users by username, email, or person name with pagination, ordering, and role filtering.

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
| `search` | string | No | - | Search query for username, email, or person name |
| `role_names` | array | No | - | Filter users by role names (e.g., ["admin"]) |

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
      "roles": ["user", "admin"]
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
- Searches `username`, `email`, and person's `first_name`/`second_name` fields with OR logic
- Pattern matching: `%query%` (matches anywhere in text)
- `role_names` can be used as query parameter multiple times (e.g., `?role_names=admin&role_names=user`)

**Examples:**

1. **Search users by name:**
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
GET /api/users/search?order_by=email&ascending=false&page=1&items_per_page=20
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Bad Request - invalid query parameters |
| 500 | Internal Server Error - server error |

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

Use this endpoint when displaying football plays in the scoreboard or play-by-play view where player information (name, photo, position, team) is needed for each event.

**Error Responses:**

- **404 Not Found** - Match doesn't exist
- **500 Internal Server Error** - Server error

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
