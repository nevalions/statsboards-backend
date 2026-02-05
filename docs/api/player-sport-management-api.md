# Player Sport Management API

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
