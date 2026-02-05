# Player Detail Context API

These endpoints provide player details with context-specific data based on where the player is being viewed from (sport, tournament, team, or match). Each endpoint returns person data with photos, sport info, relevant context assignment, and full career data in a single optimized API call.

### GET /api/players/id/{player_id}/in-tournament/{tournament_id}

Get player details in tournament context. Returns person with photos, sport info, specific tournament assignment (team, position, player number), and full career data.

**Endpoint:**
```
GET /api/players/id/{player_id}/in-tournament/{tournament_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `player_id` | integer | Yes | Player ID to fetch details for |
| `tournament_id` | integer | Yes | Tournament ID context |

**Response (200 OK):**
```json
{
  "id": 1,
  "sport_id": 1,
  "person": {
    "id": 123,
    "person_eesl_id": null,
    "first_name": "John",
    "second_name": "Doe",
    "person_photo_url": "/static/uploads/persons/photos/123.jpg",
    "person_photo_icon_url": "/static/uploads/persons/icons/123.jpg",
    "person_photo_web_url": "/static/uploads/persons/web/123.jpg",
    "person_dob": "1990-01-15T00:00:00"
  },
  "sport": {
    "id": 1,
    "title": "Football"
  },
  "tournament_assignment": {
    "team_id": 5,
    "team_title": "FC Barcelona",
    "position_id": 3,
    "position_title": "Forward",
    "player_number": "10",
    "tournament_title": "La Liga 2024",
    "tournament_year": "2024",
    "tournament_id": 2
  },
  "career_by_team": [
    {
      "team_id": 5,
      "team_title": "FC Barcelona",
      "assignments": [
        {
          "id": 101,
          "team_id": 5,
          "team_title": "FC Barcelona",
          "position_id": 3,
          "position_title": "Forward",
          "player_number": "10",
          "tournament_id": 2,
          "tournament_title": "La Liga 2024",
          "season_id": 2,
          "season_year": 2024
        }
      ]
    }
  ],
  "career_by_tournament": [
    {
      "tournament_id": 2,
      "tournament_title": "La Liga 2024",
      "season_id": 2,
      "season_year": 2024,
      "assignments": [
        {
          "id": 101,
          "team_id": 5,
          "team_title": "FC Barcelona",
          "position_id": 3,
          "position_title": "Forward",
          "player_number": "10",
          "tournament_id": 2,
          "tournament_title": "La Liga 2024",
          "season_id": 2,
          "season_year": 2024
        }
      ]
    }
  ]
}
```

**Response Schema:**

```typescript
interface PlayerDetailInTournamentResponse {
  id: number;
  sport_id: number;
  person: Person;
  sport: Sport;
  tournament_assignment: TournamentAssignment;
  career_by_team: CareerByTeam[];
  career_by_tournament: CareerByTournament[];
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

interface Sport {
  id: number;
  title: string;
}

interface TournamentAssignment {
  team_id: number | null;
  team_title: string | null;
  position_id: number | null;
  position_title: string | null;
  player_number: string | null;
  tournament_title: string | null;
  tournament_year: string | null;
  tournament_id: number | null;
}

interface CareerByTeam {
  team_id: number | null;
  team_title: string | null;
  assignments: TeamAssignment[];
}

interface CareerByTournament {
  tournament_id: number | null;
  tournament_title: string | null;
  season_id: number | null;
  season_year: number | null;
  assignments: TeamAssignment[];
}

interface TeamAssignment {
  id: number;
  team_id: number | null;
  team_title: string | null;
  position_id: number | null;
  position_title: string | null;
  player_number: string | null;
  tournament_id: number | null;
  tournament_title: string | null;
  season_id: number | null;
  season_year: number | null;
}
```

**Behavior:**

- Returns player details with person (including photos) and sport information
- Includes specific tournament assignment for the given tournament context
- Includes full career data grouped by team and by tournament/season
- All relationships (person, sport, team, position, tournament, season) are loaded in a single optimized query
- Player must exist and must be assigned to the specified tournament
- `career_by_team` is sorted alphabetically by team title
- `career_by_tournament` is sorted chronologically by season year (newest first)

**Use Cases:**

- **Player detail page from tournament view**: Display player information when navigating from tournament roster
- **Tournament context player details**: Show player's specific role and assignment in that tournament
- **Optimized single API call**: Replace multiple calls (person + career) with one optimized endpoint

**Examples:**

1. **Get player details in tournament context:**
```
GET /api/players/id/1/in-tournament/2
```

2. **Display tournament player details:**
```typescript
async function loadPlayerDetailInTournament(playerId: number, tournamentId: number) {
  const response = await fetch(
    `/api/players/id/${playerId}/in-tournament/${tournamentId}`
  );
  const data: PlayerDetailInTournamentResponse = await response.json();
  
  return {
    player: data.person,
    sport: data.sport,
    tournamentContext: data.tournament_assignment,
    career: {
      byTeam: data.career_by_team,
      byTournament: data.career_by_tournament
    }
  };
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - player details returned |
| 404 | Not Found - player_id doesn't exist OR player not assigned to tournament_id |
| 500 | Internal Server Error - server error |

**Notes:**

- This is a PRIORITY endpoint for player detail views accessed from tournament pages
- Replaces the need for calling `/api/players/id/{player_id}/person` AND `/api/players/id/{player_id}/career` separately
- Frontend can use a single component with context-aware routing
- See [Player Career API](#player-career-api) for details on career data structure

**Related Issues:**

- STAB-79: Create context-specific backend endpoints for player detail (parent)
 
---
