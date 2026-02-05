# Available Teams for Tournament API

### GET /api/tournaments/id/{tournament_id}/teams/available

Get all teams in a tournament's sport who are not already connected to the tournament. This endpoint is designed for dropdown selection of available teams to add to a tournament.

**Endpoint:**
```
GET /api/tournaments/id/{tournament_id}/teams/available
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tournament_id` | integer | Yes | Tournament ID |

**Response (200 OK):**

```json
[
  {
    "id": 1,
    "team_eesl_id": 12345,
    "title": "Team Alpha",
    "city": "Boston",
    "description": "Professional sports team",
    "team_logo_url": "/static/uploads/teams/logos/1.jpg",
    "team_logo_icon_url": "/static/uploads/teams/icons/1.jpg",
    "team_logo_web_url": "/static/uploads/teams/web/1.jpg",
    "team_color": "#FF0000",
    "sponsor_line_id": null,
    "main_sponsor_id": 5,
    "sport_id": 1
  },
  {
    "id": 2,
    "team_eesl_id": 12346,
    "title": "Team Beta",
    "city": "New York",
    "description": "Another sports team",
    "team_logo_url": "/static/uploads/teams/logos/2.jpg",
    "team_logo_icon_url": "/static/uploads/teams/icons/2.jpg",
    "team_logo_web_url": "/static/uploads/teams/web/2.jpg",
    "team_color": "#0000FF",
    "sponsor_line_id": null,
    "main_sponsor_id": 6,
    "sport_id": 1
  }
]
```

**Response Schema:**

```typescript
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

- Retrieves all teams whose `sport_id` matches the tournament's `sport_id`
- Excludes teams who already have a `TeamTournament` connection to this tournament
- Returns teams sorted by `title` (alphabetical order)
- Returns empty array if tournament doesn't exist or no available teams
- No pagination - returns all matching teams in a single response

**Use Cases:**

- **Team selection dropdown**: When adding teams to a tournament
- **Tournament administration**: Finding eligible teams to join tournament
- **Tournament setup**: Selecting teams from the sport to participate

**Examples:**

1. **Get available teams for tournament:**
```
GET /api/tournaments/id/5/teams/available
```

2. **Use in dropdown for adding teams:**
```typescript
async function loadAvailableTeams(tournamentId: number) {
  const response = await fetch(
    `/api/tournaments/id/${tournamentId}/teams/available`
  );
  const teams: Team[] = await response.json();
  
  // Render dropdown
  return teams.map(team => ({
    value: team.id,
    label: team.title,
    logo: team.team_logo_icon_url
  }));
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 200 | Success - available teams returned (empty array if none) |
| 500 | Internal Server Error - server error |

**Note:** Returns empty array (200 OK) instead of 404 if tournament doesn't exist, making it safe for dropdown use cases.

---
