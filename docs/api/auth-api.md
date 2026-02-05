# Auth API

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
