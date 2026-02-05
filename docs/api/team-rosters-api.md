# Team Rosters API

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
