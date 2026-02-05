# Available Players for Team in Match API

### GET /api/matches/id/{match_id}/team/{team_id}/available-players/

Get all players in a team's tournament roster who are not already connected to a specific match. This endpoint is designed for dropdown selection of available players when adding players to a match roster.

**Endpoint:**
```
GET /api/matches/id/{match_id}/team/{team_id}/available-players/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID |
| `team_id` | integer | Yes | Team ID |

**Response (200 OK):**

```json
[
  {
    "id": 789,
    "player_id": 791,
    "player_team_tournament": {
      "id": 789,
      "player_team_tournament_eesl_id": null,
      "player_id": 791,
      "position_id": 10,
      "team_id": 1,
      "tournament_id": 5,
      "player_number": "8"
    },
    "player": {
      "id": 791,
      "sport_id": 1,
      "person_id": 125,
      "player_eesl_id": 12347
    },
    "person": {
      "id": 125,
      "person_eesl_id": null,
      "first_name": "Backup",
      "second_name": "Quarterback",
      "person_photo_url": "/static/uploads/persons/photos/125.jpg",
      "person_photo_icon_url": "/static/uploads/persons/icons/125.jpg",
      "person_photo_web_url": "/static/uploads/persons/web/125.jpg",
      "person_dob": "1995-06-15T00:00:00"
    },
    "position": {
      "id": 10,
      "title": "Quarterback",
      "category": "offense",
      "sport_id": 1
    },
    "team": {
      "id": 1,
      "team_eesl_id": 12345,
      "title": "Team A",
      "city": "Boston",
      "description": "Professional football team",
      "team_logo_url": "/static/uploads/teams/logos/1.jpg",
      "team_logo_icon_url": "/static/uploads/teams/icons/1.jpg",
      "team_logo_web_url": "/static/uploads/teams/web/1.jpg",
      "team_color": "#FF0000",
      "sponsor_line_id": null,
      "main_sponsor_id": 5,
      "sport_id": 1
    },
    "player_number": "8"
  }
]
```

**Response Schema:**

```typescript
interface AvailablePlayerMatch {
  id: number;
  player_id: number | null;
  player_team_tournament: PlayerTeamTournament;
  player: Player | null;
  person: Person | null;
  position: Position | null;
  team: Team | null;
  player_number: string;
}

interface PlayerTeamTournament {
  id: number;
  player_team_tournament_eesl_id: number | null;
  player_id: number | null;
  position_id: number | null;
  team_id: number | null;
  tournament_id: number | null;
  player_number: string;
}

interface Player {
  id: number;
  sport_id: number | null;
  person_id: number | null;
  player_eesl_id: number | null;
}

interface Person {
  id: number;
  person_eesl_id: number | null;
  first_name: string;
  second_name: string;
  person_photo_url: string | null;
  person_photo_icon_url: string | null;
  person_photo_web_url: string | null;
  person_dob: string | null;
}

interface Position {
  id: number;
  title: string;
  category: 'offense' | 'defense' | 'special' | 'other' | null;
  sport_id: number;
}

interface Team {
  id: number;
  team_eesl_id: number | null;
  title: string;
  city: string | null;
  description: string | null;
  team_logo_url: string | null;
  team_logo_icon_url: string | null;
  team_logo_web_url: string | null;
  team_color: string;
  sponsor_line_id: number | null;
  main_sponsor_id: number | null;
  sport_id: number;
}
```

**Behavior:**

- Retrieves all `PlayerTeamTournament` records matching the team_id and match's tournament_id
- Excludes players who already have a `PlayerMatch` connection to this match
- Returns players with full related data: player, person, position, team
- Returns empty array if match doesn't exist or no available players
- Designed for efficient dropdown rendering with all necessary data pre-loaded

**Use Cases:**

- **Player selection dropdown**: When adding players to a match roster
- **Substitution management**: Finding bench players available for substitution
- **Match administration**: Managing match rosters by adding/removing players

**Examples:**

1. **Get available players for team in match:**
```
GET /api/matches/id/123/team/1/available-players/
```

2. **Use in dropdown for adding players to match:**
```typescript
async function loadAvailablePlayers(matchId: number, teamId: number) {
  const response = await fetch(
    `/api/matches/id/${matchId}/team/${teamId}/available-players/`
  );
  const players: AvailablePlayerMatch[] = await response.json();
  
  // Render dropdown
  return players.map(player => ({
    value: player.player_team_tournament.id,
    label: `${player.person?.first_name} ${player.person?.second_name} (${player.player_number})`,
    avatar: player.person?.person_photo_icon_url,
    position: player.position?.title
  }));
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - available players returned (empty array if none) |
| 404 | Not Found - match doesn't exist |
| 500 | Internal Server Error - server error |

**Note:** Returns empty array (200 OK) instead of 404 if match doesn't exist, making it safe for dropdown use cases without requiring error handling.

---
