# Available Players for Tournament API

### GET /api/tournaments/id/{tournament_id}/players/available

Get all players in a tournament's sport who are not already connected to the tournament. This endpoint is designed for dropdown selection of available players to add to a tournament.

**Endpoint:**
```
GET /api/tournaments/id/{tournament_id}/players/available
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tournament_id` | integer | Yes | Tournament ID |

**Response (200 OK):**

```json
[
  {
    "id": 789,
    "sport_id": 1,
    "person_id": 123,
    "player_eesl_id": 98765,
    "person": {
      "id": 123,
      "person_eesl_id": null,
      "first_name": "John",
      "second_name": "Doe",
      "person_photo_url": "/static/uploads/persons/photos/123.jpg",
      "person_photo_icon_url": "/static/uploads/persons/icons/123.jpg",
      "person_photo_web_url": "/static/uploads/persons/web/123.jpg",
      "person_dob": "1990-01-15T00:00:00"
    }
  },
  {
    "id": 790,
    "sport_id": 1,
    "person_id": 124,
    "player_eesl_id": 98766,
    "person": {
      "id": 124,
      "person_eesl_id": null,
      "first_name": "Jane",
      "second_name": "Smith",
      "person_photo_url": "/static/uploads/persons/photos/124.jpg",
      "person_photo_icon_url": "/static/uploads/persons/icons/124.jpg",
      "person_photo_web_url": "/static/uploads/persons/web/124.jpg",
      "person_dob": "1992-03-22T00:00:00"
    }
  }
]
```

**Response Schema:**

```typescript
interface PlayerWithPerson {
  id: number;
  sport_id: number | null;
  person_id: number | null;
  player_eesl_id: number | null;
  person: Person;
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
```

**Behavior:**

- Retrieves all players whose `sport_id` matches tournament's `sport_id`
- Excludes players who already have a `PlayerTeamTournament` connection to this tournament
- Returns players with person details pre-loaded for efficient dropdown display
- Results are sorted by player name (second_name, then first_name) in ascending alphabetical order
- Returns empty array if tournament doesn't exist or no available players

**Use Cases:**

- **Player selection dropdown**: When adding players to a tournament roster
- **Roster management**: When adding new players to a tournament without duplicates
- **Tournament administration**: Finding eligible players to join tournament

**Examples:**

1. **Get available players for tournament:**
```
GET /api/tournaments/id/5/players/available
```

2. **Use in dropdown for adding players:**
```typescript
async function loadAvailablePlayers(tournamentId: number) {
  const response = await fetch(
    `/api/tournaments/id/${tournamentId}/players/available`
  );
  const players: PlayerWithPerson[] = await response.json();
  
  // Render dropdown
  return players.map(player => ({
    value: player.id,
    label: `${player.person.first_name} ${player.person.second_name}`,
    avatar: player.person.person_photo_icon_url
  }));
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - available players returned (empty array if none) |
| 500 | Internal Server Error - server error |

**Note:** Returns empty array (200 OK) instead of 404 if tournament doesn't exist, making it safe for dropdown use cases.

---
