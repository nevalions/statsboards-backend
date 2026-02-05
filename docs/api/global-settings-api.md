# Global Settings API

Manage global system settings and seasons. These endpoints control application configuration and tournament seasons.

### Settings Endpoints

#### GET /api/settings/grouped

Get all settings grouped by category. Returns organized settings for frontend consumption.

**Endpoint:**
```
GET /api/settings/grouped
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "category": "ui",
      "settings": [
        {
          "id": 1,
          "key": "theme.default",
          "value": "dark",
          "value_type": "string",
          "category": "ui",
          "description": "Default application theme",
          "updated_at": "2024-01-15T10:30:00Z"
        }
      ]
    },
    {
      "category": "notifications",
      "settings": [
        {
          "id": 2,
          "key": "notifications.enabled",
          "value": "true",
          "value_type": "boolean",
          "category": "notifications",
          "description": "Enable email notifications",
          "updated_at": "2024-01-15T11:00:00Z"
        }
      ]
    }
  ]
}
```

**Response Schema:**
```typescript
interface GlobalSettingsGroupedResponse {
  data: GlobalSettingsGroupedSchema[];
}

interface GlobalSettingsGroupedSchema {
  category: string;
  settings: GlobalSettingSchema[];
}

interface GlobalSettingSchema {
  id: number;
  key: string;
  value: string;
  value_type: string;
  category: string | null;
  description: string | null;
  updated_at: string;
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

#### GET /api/settings/category/{category}

Get all settings in a specific category.

**Endpoint:**
```
GET /api/settings/category/{category}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | Yes | Category name to filter settings |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "key": "theme.default",
    "value": "dark",
    "value_type": "string",
    "category": "ui",
    "description": "Default application theme",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

**Response Schema:**
```typescript
interface GlobalSettingSchema {
  id: number;
  key: string;
  value: string;
  value_type: string;
  category: string | null;
  description: string | null;
  updated_at: string;
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

#### GET /api/settings/value/{key}

Get a specific setting value with type conversion. Returns the raw value as a string.

**Endpoint:**
```
GET /api/settings/value/{key}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | string | Yes | Setting key to retrieve |

**Response (200 OK):**
```json
{
  "value": "dark"
}
```

**Response Schema:**
```typescript
interface GlobalSettingValueSchema {
  value: string;
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Setting not found - key does not exist |
| 500 | Internal server error |

---

#### POST /api/settings/

Create a new global setting. Requires admin role.

**Endpoint:**
```
POST /api/settings/
```

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "key": "theme.default",
  "value": "dark",
  "value_type": "string",
  "category": "ui",
  "description": "Default application theme"
}
```

**Request Schema:**
```typescript
interface GlobalSettingSchemaCreate {
  key: string; // Max 100 characters, unique
  value: string;
  value_type: string; // Max 20 characters (e.g., "string", "boolean", "number")
  category: string | null; // Max 50 characters, optional
  description: string | null; // Optional description
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "key": "theme.default",
  "value": "dark",
  "value_type": "string",
  "category": "ui",
  "description": "Default application theme",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 422 | Validation error - invalid request data |
| 500 | Internal server error |

---

#### PUT /api/settings/{item_id}/

Update a global setting by ID. Requires admin role.

**Endpoint:**
```
PUT /api/settings/{item_id}/
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Setting ID to update |

**Request Body:**
```json
{
  "key": "theme.default",
  "value": "light",
  "value_type": "string",
  "category": "ui",
  "description": "Updated default application theme"
}
```

**Request Schema:**
```typescript
interface GlobalSettingSchemaUpdate {
  key: string | null; // Optional - max 100 characters
  value: string | null; // Optional
  value_type: string | null; // Optional - max 20 characters
  category: string | null; // Optional - max 50 characters
  description: string | null; // Optional
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "key": "theme.default",
  "value": "light",
  "value_type": "string",
  "category": "ui",
  "description": "Updated default application theme",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 404 | Setting not found |
| 422 | Validation error - invalid request data |
| 500 | Internal server error |

---

#### DELETE /api/settings/id/{model_id}

Delete a global setting by ID. Requires admin role.

**Endpoint:**
```
DELETE /api/settings/id/{model_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | Setting ID to delete |

**Response (200 OK):**
```json
{
  "detail": "Setting 1 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - user does not have admin role |
| 500 | Internal server error |

---

### Season Endpoints

Seasons are managed through the settings API. These endpoints allow CRUD operations for tournament seasons.

#### GET /api/settings/seasons/

Get all seasons ordered by year.

**Endpoint:**
```
GET /api/settings/seasons/
```

**Response (200 OK):**
```json
[
  {
    "id": 2,
    "year": 2024,
    "description": "2024 Season",
    "iscurrent": true
  },
  {
    "id": 1,
    "year": 2023,
    "description": "2023 Season",
    "iscurrent": false
  }
]
```

**Response Schema:**
```typescript
interface SeasonSchema {
  id: number;
  year: number; // 1900-2999
  description: string | null;
  iscurrent: boolean;
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 500 | Internal server error |

---

#### GET /api/settings/seasons/id/{item_id}/

Get a season by ID.

**Endpoint:**
```
GET /api/settings/seasons/id/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Season ID to retrieve |

**Response (200 OK):**
```json
{
  "id": 2,
  "year": 2024,
  "description": "2024 Season",
  "iscurrent": true
}
```

**Response Schema:**
```typescript
interface SeasonSchema {
  id: number;
  year: number; // 1900-2999
  description: string | null;
  iscurrent: boolean;
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Season not found |
| 500 | Internal server error |

---

#### POST /api/settings/seasons/

Create a new season.

**Endpoint:**
```
POST /api/settings/seasons/
```

**Request Body:**
```json
{
  "year": 2024,
  "description": "2024 Season",
  "iscurrent": true
}
```

**Request Schema:**
```typescript
interface SeasonSchemaCreate {
  year: number; // 1900-2999
  description: string | null; // Optional description
  iscurrent: boolean; // Whether this is the current season (default: false)
}
```

**Response (200 OK):**
```json
{
  "id": 2,
  "year": 2024,
  "description": "2024 Season",
  "iscurrent": true
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 422 | Validation error - invalid request data (e.g., year out of range) |
| 500 | Internal server error |

---

#### PUT /api/settings/seasons/{item_id}/

Update a season by ID.

**Endpoint:**
```
PUT /api/settings/seasons/{item_id}/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Season ID to update |

**Request Body:**
```json
{
  "description": "Updated 2024 Season",
  "iscurrent": false
}
```

**Request Schema:**
```typescript
interface SeasonSchemaUpdate {
  year: number | null; // Optional - 1900-2999
  description: string | null; // Optional description
  iscurrent: boolean | null; // Optional
}
```

**Response (200 OK):**
```json
{
  "id": 2,
  "year": 2024,
  "description": "Updated 2024 Season",
  "iscurrent": false
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Season not found |
| 422 | Validation error - invalid request data |
| 500 | Internal server error |

---

#### DELETE /api/settings/seasons/id/{model_id}

Delete a season by ID.

**Endpoint:**
```
DELETE /api/settings/seasons/id/{model_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | integer | Yes | Season ID to delete |

**Response (200 OK):**
```json
{
  "detail": "Season 2 deleted successfully"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Season not found |
| 500 | Internal server error |

---

### Usage Examples

**1. Get grouped settings for frontend:**
```bash
GET /api/settings/grouped
```

**2. Get all UI settings:**
```bash
GET /api/settings/category/ui
```

**3. Get a specific setting value:**
```bash
GET /api/settings/value/theme.default
```

**4. Create a new setting (admin):**
```bash
POST /api/settings/
Authorization: Bearer <token>

{
  "key": "notifications.enabled",
  "value": "true",
  "value_type": "boolean",
  "category": "notifications",
  "description": "Enable email notifications"
}
```

**5. Update a setting (admin):**
```bash
PUT /api/settings/1/
Authorization: Bearer <token>

{
  "value": "light"
}
```

**6. Get all seasons ordered by year:**
```bash
GET /api/settings/seasons/
```

**7. Get the current season:**
```bash
GET /api/settings/seasons/
# Then filter by iscurrent: true on frontend
```

**8. Create a new season:**
```bash
POST /api/settings/seasons/

{
  "year": 2025,
  "description": "2025 Season",
  "iscurrent": true
}
```

---
