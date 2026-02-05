# Privacy and User Ownership Filtering

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
