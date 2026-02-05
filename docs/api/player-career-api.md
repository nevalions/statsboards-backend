# Player Career API

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
