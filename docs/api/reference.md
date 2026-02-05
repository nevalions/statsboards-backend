# Reference and Examples

This content was split out of `docs/API_DOCUMENTATION.md` to keep the API docs easier to navigate.

## Error Responses

All API endpoints return consistent error responses.

### Standard Error Structure

```typescript
interface ErrorResponse {
  detail: string;
  success: boolean;
  request_id?: string;
  type?: string;
  [key: string]: any;
}
```

### HTTP Status Codes

| Status Code | Description | Example Scenarios |
|-------------|-------------|-------------------|
| 200 | Success | Request successful |
| 400 | Bad Request | Validation error, invalid data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Duplicate resource, creation failed |
| 422 | Unprocessable Entity | Business logic violation |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | External service failure |

### Example Error Responses

```json
{
  "detail": "Match 123 not found",
  "success": false,
  "type": "NotFoundError",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

```json
{
  "detail": "Validation error: match_number must be at most 10 characters",
  "success": false,
  "type": "ValidationError",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

```json
{
  "detail": "Conflict - player match creation failed",
  "success": false,
  "type": "IntegrityError",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### GET /api/matches/id/{match_id}/full-context/

Get all data needed for match initialization: match, teams, sport with positions, tournament, players (home roster, away roster, available home, available away).

**Endpoint:**
```
GET /api/matches/id/{match_id}/full-context/
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID |

**Response (200 OK):**

```json
{
  "match": {
    "id": 123,
    "match_eesl_id": 100,
    "team_a_id": 1,
    "team_b_id": 2,
    "tournament_id": 5,
    "sport_id": 1,
    "match_date": "2025-01-03T10:00:00",
    "week": 1
  },
  "teams": {
    "home": {
      "id": 1,
      "title": "Team A",
      "team_logo_url": "https://...",
      "team_color": "#ff0000"
    },
    "away": {
      "id": 2,
      "title": "Team B",
      "team_logo_url": "https://...",
      "team_color": "#0000ff"
    }
  },
  "sport": {
    "id": 1,
    "title": "American Football",
    "description": "Football rules...",
    "positions": [
      {
        "id": 1,
        "title": "Quarterback",
        "sport_id": 1
      },
      {
        "id": 2,
        "title": "Linebacker",
        "sport_id": 1
      }
    ]
  },
  "tournament": {
    "id": 5,
    "title": "Tournament 2026",
    "sport_id": 1,
    "season_id": 1
  },
  "players": {
    "home_roster": [
      {
        "id": 456,
        "player_id": 789,
        "match_player": {
          "id": 456,
          "match_number": "10",
          "team_id": 1,
          "match_position_id": 1
        },
        "player_team_tournament": {
          "id": 789,
          "player_id": 789,
          "team_id": 1,
          "tournament_id": 5,
          "position_id": 1
        },
        "player": {
          "id": 789,
          "person_id": 456,
          "sport_id": 1
        },
        "person": {
          "id": 456,
          "first_name": "John",
          "second_name": "Doe",
          "person_photo_url": "https://..."
        },
        "position": {
          "id": 1,
          "title": "Quarterback",
          "sport_id": 1
        },
        "team": {
          "id": 1,
          "title": "Team A"
        }
      }
    ],
    "away_roster": [],
    "available_home": [],
    "available_away": [
      {
        "id": 790,
        "player_id": 790,
        "player_team_tournament": {
          "id": 790,
          "player_id": 790,
          "team_id": 2,
          "tournament_id": 5,
          "position_id": 2
        },
        "person": {
          "id": 457,
          "first_name": "Jane",
          "second_name": "Smith",
          "person_photo_url": "https://..."
        },
        "position": {
          "id": 2,
          "title": "Linebacker",
          "sport_id": 1
        },
        "team": {
          "id": 2,
          "title": "Team B"
        }
      }
    ]
  }
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Match not found |
| 500 | Internal server error |

### GET /api/matches/id/{match_id}/comprehensive/

Get all match data including match info, match data, teams, players with person data, events, and scoreboard. This is the maximum data endpoint for scoreboard control.

**Endpoint:**
```
GET /api/matches/id/{match_id}/comprehensive/
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID |

**Response (200 OK):**

```json
{
  "match": {
    "id": 123,
    "match_eesl_id": 100,
    "team_a_id": 1,
    "team_b_id": 2,
    "tournament_id": 5,
    "match_date": "2025-01-03T10:00:00",
    "week": 1,
    "isprivate": false
  },
  "match_data": {
    "id": 1,
    "match_id": 123,
    "score_team_a": 14,
    "score_team_b": 10,
    "game_status": "in-progress",
    "qtr": "3rd",
    "ball_on": 35,
    "down": "2nd",
    "distance": "7",
    "timeout_team_a": "●●",
    "timeout_team_b": "●●●",
    "field_length": 92
  },
  "teams": {
    "team_a": {
      "id": 1,
      "title": "Team A",
      "city": "City A",
      "team_color": "#ff0000",
      "team_logo_url": "https://...",
      "team_logo_icon_url": "https://...",
      "team_logo_web_url": "https://..."
    },
    "team_b": {
      "id": 2,
      "title": "Team B",
      "city": "City B",
      "team_color": "#0000ff",
      "team_logo_url": "https://...",
      "team_logo_icon_url": "https://...",
      "team_logo_web_url": "https://..."
    }
  },
  "players": [
    {
      "id": 456,
      "team_id": 1,
      "match_id": 123,
      "player_team_tournament_id": 789,
      "player_id": 789,
      "player": {
        "id": 789,
        "player_eesl_id": 12345,
        "person_id": 123
      },
      "team": {
        "id": 1,
        "title": "Team A",
        "team_color": "#FF0000"
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
        "person_photo_url": "https://..."
      },
      "is_starting": true,
      "starting_type": "offense"
    }
  ],
  "events": [
    {
      "id": 1,
      "match_id": 123,
      "event_number": 1,
      "event_qtr": 1,
      "ball_on": 20,
      "play_type": "pass",
      "play_result": "complete",
      "score_result": "touchdown",
      "event_qb": 456,
      "pass_received_player": 457,
      "run_player": null,
      "kick_player": null,
      "offense_team": 1
    }
  ],
  "scoreboard": {
    "id": 1,
    "match_id": 123,
    "is_qtr": true,
    "is_time": true,
    "is_playclock": true,
    "is_downdistance": true,
    "is_tournament_logo": true,
    "is_main_sponsor": true,
    "is_sponsor_line": true,
    "team_a_game_color": "#ff0000",
    "team_b_game_color": "#0000ff",
    "team_a_game_title": "Team A",
    "team_b_game_title": "Team B",
    "scale_tournament_logo": 2.0,
    "scale_main_sponsor": 2.0,
    "scale_logo_a": 2.0,
    "scale_logo_b": 2.0,
    "is_flag": false,
    "is_goal_team_a": false,
    "is_goal_team_b": false,
    "is_timeout_team_a": false,
    "is_timeout_team_b": false
  }
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 404 | Match not found |
| 500 | Internal server error |

**Use Cases:**
- Scoreboard control interface needs all match data
- Real-time statistics display
- Match replay systems
- Analytics and reporting

**Notes:**
- This endpoint provides the maximum amount of match data in a single request
- Uses optimized loading strategies (selectinload) for performance
- All data fetched in minimal number of queries

---

## Integration Examples

### Example 1: Connect to Match Stats WebSocket

```typescript
async function connectToMatchStats(matchId: number) {
  const ws = new WebSocket(`ws://localhost:9000/api/matches/ws/matches/${matchId}/stats`);

  ws.onopen = () => {
    console.log('Connected to match stats WebSocket');
  };

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    switch (message.type) {
      case 'full_stats_update':
        console.log('Initial stats received:', message.stats);
        // Update UI with initial stats
        break;

      case 'stats_update':
        console.log('Stats updated:', message.stats);
        // Update UI with new stats
        break;

      case 'stats_sync':
        console.log('Sync required:', message.stats);
        // Update UI with server's current stats (client update rejected)
        break;

      default:
        console.warn('Unknown message type:', message.type);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = () => {
    console.log('WebSocket connection closed');
  };

  return ws;
}

// Usage
const matchId = 123;
const wsConnection = connectToMatchStats(matchId);
```

### Example 2: Update Stats via WebSocket

```typescript
function updateStats(ws: WebSocket, matchId: number, newStats: any) {
  const message = {
    type: 'stats_update',
    match_id: matchId,
    stats: newStats,
    timestamp: new Date().toISOString()
  };

  ws.send(JSON.stringify(message));
}

// Usage
updateStats(wsConnection, 123, {
  match_id: 123,
  team_a: {
    id: 1,
    team_stats: {
      offence_yards: 260,
      pass_att: 21
    }
  },
  team_b: { /* unchanged */ }
});
```

### Example 3: Fetch Players with Full Data

```typescript
async function fetchMatchPlayers(matchId: number) {
  try {
    const response = await fetch(
      `http://localhost:9000/api/matches/id/${matchId}/players_fulldata/`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Players fetched:', data.players);

    return data.players;
  } catch (error) {
    console.error('Failed to fetch players:', error);
    throw error;
  }
}

// Usage
fetchMatchPlayers(123)
  .then(players => {
    // Process players data
    players.forEach(player => {
      console.log(`${player.person?.first_name} ${player.person?.second_name} - ${player.position?.title}`);
    });
  })
  .catch(error => {
    // Handle error
  });
```

### Example 4: Display Team Stats

```typescript
interface TeamStatsDisplay {
  teamName: string;
  totalYards: number;
  passYards: number;
  runYards: number;
  avgYardsPerAtt: number;
  thirdDownEff: string;
  fourthDownEff: string;
  turnovers: number;
}

function formatTeamStats(teamStats: any): TeamStatsDisplay {
  const thirdDownPct = teamStats.third_down_attempts > 0
    ? ((teamStats.third_down_conversions / teamStats.third_down_attempts) * 100).toFixed(1)
    : '0.0';

  const fourthDownPct = teamStats.fourth_down_attempts > 0
    ? ((teamStats.fourth_down_conversions / teamStats.fourth_down_attempts) * 100).toFixed(1)
    : '0.0';

  return {
    teamName: `Team ${teamStats.id}`,
    totalYards: teamStats.offence_yards,
    passYards: teamStats.pass_yards,
    runYards: teamStats.run_yards,
    avgYardsPerAtt: teamStats.avg_yards_per_att,
    thirdDownEff: `${thirdDownPct}%`,
    fourthDownEff: `${fourthDownPct}%`,
    turnovers: teamStats.turnovers
  };
}

// Usage in component
function renderTeamStats(teamStats: any) {
  const stats = formatTeamStats(teamStats);

  return `
    <div class="team-stats">
      <h3>${stats.teamName}</h3>
      <div class="stat-row">
        <span>Total Yards:</span>
        <span>${stats.totalYards}</span>
      </div>
      <div class="stat-row">
        <span>Pass Yards:</span>
        <span>${stats.passYards}</span>
      </div>
      <div class="stat-row">
        <span>Run Yards:</span>
        <span>${stats.runYards}</span>
      </div>
      <div class="stat-row">
        <span>Avg/Att:</span>
        <span>${stats.avgYardsPerAtt}</span>
      </div>
      <div class="stat-row">
        <span>3rd Down:</span>
        <span>${stats.thirdDownEff}</span>
      </div>
      <div class="stat-row">
        <span>4th Down:</span>
        <span>${stats.fourthDownEff}</span>
      </div>
      <div class="stat-row">
        <span>Turnovers:</span>
        <span>${stats.turnovers}</span>
      </div>
    </div>
  `;
}
```

### Example 5: React Hook for Match Stats

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';

interface MatchStats {
  match_id: number;
  team_a: {
    id: number;
    team_stats: any;
    offense_stats: any;
    qb_stats: any;
    defense_stats: any;
  };
  team_b: {
    id: number;
    team_stats: any;
    offense_stats: any;
    qb_stats: any;
    defense_stats: any;
  };
}

export function useMatchStats(matchId: number) {
  const [stats, setStats] = useState<MatchStats | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Update stats via WebSocket
  const updateStats = useCallback((newStats: Partial<MatchStats>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'stats_update',
        match_id: matchId,
        stats: newStats,
        timestamp: new Date().toISOString()
      }));
    }
  }, [matchId]);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:9000/api/matches/ws/matches/${matchId}/stats`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'full_stats_update':
        case 'stats_update':
          setStats(message.stats);
          break;

        case 'stats_sync':
          setStats(message.stats);
          console.warn('Stats sync: server rejected client update');
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    ws.onclose = () => {
      setConnected(false);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [matchId]);

  return { stats, connected, updateStats };
}

// Usage
function MatchStatsComponent({ matchId }: { matchId: number }) {
  const { stats, connected, updateStats } = useMatchStats(matchId);

  if (!stats) {
    return <div>Loading stats...</div>;
  }

  return (
    <div>
      <div className="connection-status">
        Status: {connected ? 'Connected' : 'Disconnected'}
      </div>
      <div className="team-a-stats">
        <h3>Team A</h3>
        <p>Total Yards: {stats.team_a.team_stats.offence_yards}</p>
        <p>Turnovers: {stats.team_a.team_stats.turnovers}</p>
      </div>
      <div className="team-b-stats">
        <h3>Team B</h3>
        <p>Total Yards: {stats.team_b.team_stats.offence_yards}</p>
        <p>Turnovers: {stats.team_b.team_stats.turnovers}</p>
      </div>
      <button
        onClick={() => updateStats({
          match_id: matchId,
          team_a: {
            id: stats.team_a.id,
            team_stats: {
              ...stats.team_a.team_stats,
              offence_yards: stats.team_a.team_stats.offence_yards + 1
            }
          },
          team_b: stats.team_b
        })}
        disabled={!connected}
      >
        Increment Team A Yards
      </button>
    </div>
  );
}
```

---

## Notes

### WebSocket Connection Stability

- WebSocket connections may drop due to network issues
- Implement reconnection logic with exponential backoff
- Handle connection states gracefully in UI

### Timestamps

- All timestamps are in ISO 8601 format: `YYYY-MM-DDTHH:mm:ss.ssssss`
- Client timestamps should be in UTC
- Server timestamps are always UTC

### Conflict Resolution

- Client updates with older timestamps are rejected
- Server always wins in conflict scenarios
- Clients receive `stats_sync` messages with current data after conflicts
- Implement UI indicators when updates are rejected

### Performance

- Players endpoint uses single optimized query with `selectinload` for performance
- Stats are cached server-side (invalidated on updates)
- WebSocket connections are pooled per match

### Future Enhancements

- **Authentication**: WebSocket authentication support (planned)
- **Historical Stats**: Historical match statistics (planned)

---

## Support

For issues or questions regarding these APIs, please contact the backend team or create an issue in the repository.
