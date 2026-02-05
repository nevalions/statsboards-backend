# Match Parser API

Endpoints for parsing and importing matches from EESL.

### GET /api/matches/pars/tournament/{eesl_tournament_id}

Parse matches for a tournament without writing to the database.

**Endpoint:**
```
GET /api/matches/pars/tournament/{eesl_tournament_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `eesl_tournament_id` | integer | Yes | EESL tournament ID to parse |

**Response:** Parsed match data from EESL (structure depends on parser output).

---

### GET /api/matches/pars_and_create/tournament/{eesl_tournament_id}

Parse matches for a tournament and create them in the database.

**Endpoint:**
```
GET /api/matches/pars_and_create/tournament/{eesl_tournament_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `eesl_tournament_id` | integer | Yes | EESL tournament ID to parse and import |

**Response:** Parsed data with created match records (structure depends on parser output).
