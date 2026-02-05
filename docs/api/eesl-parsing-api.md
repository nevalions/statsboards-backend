# EESL Parsing APIs

Endpoints for parsing and importing data from the EESL system.

## Tournaments

### GET /api/tournaments/pars/season/{eesl_season_id}

Parse tournaments for a season (no DB writes).

Auth: none.

Minimal response shape:

```json
[
  {
    "title": "string",
    "season_id": 1,
    "sport_id": 1,
    "tournament_eesl_id": 12345
  }
]
```

### POST /api/tournaments/pars_and_create/season/{eesl_season_id}

Parse tournaments and create/update them in the DB.

Auth: none.

Query params:

- `season_id` (optional)
- `sport_id` (optional)

Minimal response shape:

```json
[
  {
    "id": 1,
    "title": "string",
    "season_id": 1,
    "sport_id": 1
  }
]
```

## Teams

### GET /api/teams/pars/tournament/{eesl_tournament_id}

Parse teams for a tournament (no DB writes).

Auth: none.

Minimal response shape:

```json
[
  {
    "title": "string",
    "team_eesl_id": 12345,
    "sport_id": 1
  }
]
```

### POST /api/teams/pars_and_create/tournament/{eesl_tournament_id}

Parse teams and create/update them in the DB, plus team-tournament links.

Auth: none.

Minimal response shape:

```json
[
  {
    "id": 1,
    "title": "string",
    "sport_id": 1
  }
]
```

## Players (All EESL)

### GET /api/players/pars/all_eesl

Parse a small sample from the EESL players index (debug endpoint; uses fixed defaults in code).

Auth: none.

Minimal response shape:

```json
[
  {
    "person": {
      "first_name": "string",
      "second_name": "string",
      "person_eesl_id": 12345
    },
    "player": {
      "sport_id": 1,
      "player_eesl_id": 12345
    }
  }
]
```

### POST /api/players/pars_and_create/all_eesl/start_page/{start_page}/season_id/{season_id}/

Parse and create players + persons from EESL starting at `start_page` for a given `season_id`.

Auth: none.

Minimal response shape:

```json
[
  {
    "id": 1,
    "username": "string",
    "person_id": 10
  }
]
```

## Player-Team-Tournament

### GET /api/players_team_tournament/pars/tournament/{tournament_id}/team/{team_id}

Parse players for a team in a tournament (no DB writes).

Auth: none.

Minimal response shape:

```json
[
  {
    "player_eesl_id": 12345,
    "player_number": "10",
    "player_position": "string",
    "eesl_team_id": 1001,
    "eesl_tournament_id": 2001
  }
]
```

### PUT /api/players_team_tournament/pars_and_create/tournament/{tournament_id}/team/id/{team_id}/players

Parse players for a team/tournament and create related persons, players, positions, and player-team-tournament entries.

Auth: none.

Minimal response shape:

```json
[
  {
    "id": 1,
    "player_id": 10,
    "team_id": 20,
    "tournament_id": 30,
    "player_number": "10"
  }
]
```

## Player-Match (EESL Match Parsing)

### GET /api/players_match/pars/match/{eesl_match_id}

Parse match roster data from EESL (no DB writes).

Auth: none.

Minimal response shape:

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

### GET /api/players_match/pars_and_create/match/{eesl_match_id}

Parse match roster data and create/update related records.

Auth: none.

Minimal response shape:

```json
[
  {
    "id": 1,
    "player_id": 10,
    "match_id": 100
  }
]
```

## Match Parsing

Match parsing endpoints are documented in `docs/api/match-parser-api.md`.
