# API Routing Conventions

All base CRUD operations follow consistent routing patterns using path parameters instead of query parameters for resource identification.

### Standard CRUD Routes

| Operation | Route Pattern | Example | Notes |
|-----------|---------------|----------|--------|
| **Create** | `POST /{resource}/` | `POST /api/teams/` | Create new resource with request body |
| **Read All** | `GET /{resource}/` | `GET /api/teams/` | List all resources (supports pagination) |
| **Read By ID** | `GET /{resource}/{item_id}/` | `GET /api/teams/5/` | Get single resource by ID |
| **Update** | `PUT /{resource}/{item_id}/` | `PUT /api/teams/5/` | Update resource by ID with request body |
| **Delete** | `DELETE /{resource}/{item_id}/` | `DELETE /api/users/456/` | Delete resource by ID (custom implementation, not auto-generated) |

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
DELETE /api/users/456/
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
