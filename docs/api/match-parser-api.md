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

### POST /api/matches/pars_and_create/tournament/{eesl_tournament_id}

Parse matches for a tournament and create them in the database.

**Endpoint:**
```
POST /api/matches/pars_and_create/tournament/{eesl_tournament_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `eesl_tournament_id` | integer | Yes | EESL tournament ID to parse and import |

**Response:** Parsed data with created match records (structure depends on parser output).

---

### GET /api/matches/pars/match/{eesl_match_id}

Parse a single match's basic data from EESL (no DB writes).

**Endpoint:**
```
GET /api/matches/pars/match/{eesl_match_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `eesl_match_id` | integer | Yes | EESL match ID to parse |

**Response:** Parsed match data from EESL (empty dict if team lookup fails).

```json
{
  "team_a": "string",
  "team_b": "string",
  "team_a_eesl_id": 1001,
  "team_b_eesl_id": 1002,
  "score_a": "0",
  "score_b": "0",
  "roster_a": [ { "player_eesl_id": 12345 } ],
  "roster_b": [ { "player_eesl_id": 12346 } ]
}
```

---

### POST /api/matches/pars_and_create/match/{eesl_match_id}

Parse a single match's basic data and create/update it in DB.

**Endpoint:**
```
POST /api/matches/pars_and_create/match/{eesl_match_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `eesl_match_id` | integer | Yes | EESL match ID to parse and import |

**Response:** Parsed data with created match record (empty array if team lookup fails).
