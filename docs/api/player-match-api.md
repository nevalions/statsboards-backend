# Player Match API

### GET /api/matches/id/{match_id}/players_fulldata/

Get all players in a match with full related data (team, person, position) in a single optimized query.

**Endpoint:**
```
GET /api/matches/id/{match_id}/players_fulldata/
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID |

**Response (200 OK):**

```json
{
  "players": [
    {
      "id": 456,
      "player_id": 789,
      "player": {
        "id": 789,
        "player_eesl_id": 12345,
        "person_id": 123
      },
      "team": {
        "id": 1,
        "title": "Team A",
        "team_color": "#FF0000",
        "logo_url": "/static/uploads/teams/logos/1.jpg"
      },
      "position": {
        "id": 10,
        "title": "Quarterback",
        "category": "offense",
        "sport_id": 1
      },
      "player_team_tournament": {
        "id": 789,
        "player_team_tournament_eesl_id": 12345,
        "player_id": 789,
        "team_id": 1,
        "tournament_id": 5,
        "position_id": 10,
        "player_number": 12
      },
      "person": {
        "id": 123,
        "first_name": "John",
        "second_name": "Doe",
        "person_photo_url": "/static/uploads/persons/photos/123.jpg",
        "person_photo_icon_url": "/static/uploads/persons/icons/123.jpg",
        "person_photo_web_url": "/static/uploads/persons/web/123.jpg"
      },
      "is_starting": true,
      "starting_type": "offense"
    },
    {
      "id": 457,
      "player_id": 790,
      "player": { /* ... */ },
      "team": { /* ... */ },
      "position": {
        "id": 11,
        "title": "Linebacker",
        "category": "defense",
        "sport_id": 1
      },
      "player_team_tournament": { /* ... */ },
      "person": { /* ... */ },
      "is_starting": false,
      "starting_type": null
    }
  ]
}
```

**Response Schema:**

```typescript
interface PlayerMatchFullData {
  players: PlayerMatchDetail[];
}

interface PlayerMatchDetail {
  id: number;
  team_id: number;
  match_id: number;
  player_team_tournament_id: number;
  player_id: number | null;
  player: {
    id: number;
    player_eesl_id: number | null;
    person_id: number;
  } | null;
  team: {
    id: number;
    title: string;
    team_color: string;
    logo_url: string | null;
  } | null;
  position: {
    id: number;
    title: string;
    category: 'offense' | 'defense' | 'special' | 'other' | null;
    sport_id: number;
  } | null;
  player_team_tournament: {
    id: number;
    player_team_tournament_eesl_id: number | null;
    player_id: number;
    team_id: number;
    tournament_id: number;
    position_id: number | null;
    player_number: string;
  } | null;
  person: {
    id: number;
    first_name: string;
    second_name: string;
    person_photo_url: string | null;
    person_photo_icon_url: string | null;
    person_photo_web_url: string | null;
  } | null;
  is_starting: boolean | null;
  starting_type: 'offense' | 'defense' | 'special' | null;
}
```

**New Fields:**

| Field | Type | Description | Values |
| -- | -- | -- | -- |
| `team_id` | number | Team ID for the player match | integer |
| `match_id` | number | Match ID for the player match | integer |
| `player_team_tournament_id` | number | PlayerTeamTournament record ID | integer |
| `position.category` | string | Position category (offense/defense/special/other) | 'offense', 'defense', 'special', 'other' |
| `is_starting` | boolean | Whether player is in starting lineup | true, false |
| `starting_type` | string | Starting lineup type | 'offense', 'defense', 'special', null |

**Response Schema:**

```typescript
interface PlayerMatchFullData {
  players: PlayerMatchDetail[];
}

interface PlayerMatchDetail {
  match_player: {
    id: number;
    player_match_eesl_id: number | null;
    player_team_tournament_id: number | null;
    match_position_id: number | null;
    match_id: number;
    match_number: string;
    team_id: number;
    is_start: boolean;
  };
  player_team_tournament: {
    id: number;
    player_team_tournament_eesl_id: number | null;
    player_id: number;
    team_id: number;
    tournament_id: number;
    position_id: number;
    player_number: string;
  };
  person: {
    id: number;
    first_name: string;
    second_name: string;
    person_photo_url: string | null;
    person_photo_icon_url: string | null;
    person_photo_web_url: string | null;
  } | null;
  position: {
    id: number;
    title: string;
    sport_id: number;
  } | null;
}
```

**Error Responses:**

- **404 Not Found** - Match doesn't exist
- **500 Internal Server Error** - Server error

---
