# WebSocket APIs

This content was split out of `docs/API_DOCUMENTATION.md` to keep the API docs easier to navigate.

## WebSocket Endpoints

### Overview

The backend provides real-time data streaming through WebSocket connections for:
- Live match data updates (scores, game clock, play clock, events)
- Match statistics with conflict resolution
- Real-time scoreboard and clock synchronization

**Important Note:** WebSocket endpoints in `README.md` are outdated. The current actual endpoints are:

| README URL | Actual URL | Status |
|-------------|--------------|--------|
| `ws://localhost:9000/ws/matchdata/{match_id}` | `/api/matches/ws/id/{match_id}/{client_id}/` | ⚠️ Outdated |
| `ws://localhost:9000/ws/scoreboard/{scoreboard_id}` | Does not exist | ⚠️ Outdated |

### WebSocket Endpoint 1: Match Data

Real-time match data streaming including scores, game clock, play clock, and football events.

#### Connection

```typescript
const ws = new WebSocket('ws://localhost:9000/api/matches/ws/id/{match_id}/{client_id}/');
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID to subscribe to |
| `client_id` | string | Yes | Unique client identifier (use UUID or user-specific ID) |

#### Authentication

**Current Status:** No authentication required

Future versions may implement WebSocket authentication through:
- Query parameters: `?token=jwt_token`
- Subprotocol headers

#### Initial Data

Upon successful connection, server sends one combined initial message with all match data:

```typescript
{
  "type": "initial-load",
  "data": {
    "match_id": 123,
    "id": 123,
    "match": {
      "id": 123,
      "title": "Team A vs Team B",
      "match_date": "2026-01-21T19:00:00Z",
      "team_a_id": 1,
      "team_b_id": 2,
      "team_a_score": 14,
      "team_b_score": 10
    },
    "teams_data": {
      "team_a": {
        "id": 1,
        "title": "Team A",
        "team_color": "#FF0000",
        "logo_url": "/static/uploads/teams/logos/1.jpg"
      },
      "team_b": {
        "id": 2,
        "title": "Team B",
        "team_color": "#0000FF",
        "logo_url": "/static/uploads/teams/logos/2.jpg"
      }
    },
    "match_data": {
      "id": 456,
      "match_id": 123,
      "field_length": 92,
      "game_status": "in-progress",
      "score_team_a": 14,
      "score_team_b": 10,
      "timeout_team_a": "●●",
      "timeout_team_b": "●●",
      "qtr": "1st",
      "period_key": "period.1",
      "ball_on": 20,
      "down": "1st",
      "distance": "10"
    },
    "scoreboard_data": {
      "id": 789,
      "match_id": 123,
      "is_qtr": true,
      "period_mode": "qtr",
      "period_count": 4,
      "period_labels_json": null,
      "is_time": true,
      "is_playclock": true,
      "is_downdistance": true,
      "team_a_game_color": "#FF0000",
      "team_b_game_color": "#0000FF",
      "team_a_game_title": "Team A",
      "team_b_game_title": "Team B"
    },
    "gameclock": {
      "id": 345,
      "match_id": 123,
      "gameclock": 720,
      "gameclock_max": 720,
      "gameclock_status": "stopped"
    },
    "playclock": {
      "id": 234,
      "match_id": 123,
      "playclock": 40,
      "playclock_status": "running",
      "started_at_ms": 1737648000000
    },
    "events": [
      {
        "id": 1,
        "match_id": 123,
        "quarter": "1st",
        "time_remaining": "12:34",
        "event_type": "run",
        "event_number": 1,
        "run_player": {
          "id": 10,
          "person": {
            "first_name": "John",
            "last_name": "Doe"
          }
        }
       }
     ],
     "players": [
       {
         "id": 1,
         "player_id": 10,
         "team_id": 1,
         "match_id": 123,
         "person": {
           "id": 100,
           "first_name": "John",
           "last_name": "Doe",
           "photo_url": "/static/uploads/persons/photos/100.jpg"
         },
         "position": {
           "id": 5,
           "title": "Quarterback",
           "category": "offense"
         },
         "is_starting": true,
         "starting_type": "starter"
       }
     ],
     "statistics": {
       "team_a": {
         "id": 1,
        "team_stats": {
          "id": 1,
          "offence_yards": 250,
          "pass_att": 20,
          "run_att": 30
        }
      },
      "team_b": {
        "id": 2,
        "team_stats": {
          "id": 2,
          "offence_yards": 200,
          "pass_att": 15,
          "run_att": 25
        }
      }
    },
    "server_time_ms": 1737648000050
  }
}
```

#### Server-Sent Messages

The following message types are sent from server to client when data changes:

| Message Type | Trigger | Description |
|--------------|----------|-------------|
| `initial-load` | On connection | Combined initial message with all match data (match, teams, clocks, events, stats) |
| `match-update` | Match data changes | Updated match information, teams, or scoreboard |
| `message-update` | Match data changes | Updated match information (legacy, use match-update) |
| `gameclock-update` | Game clock changes | Updated game clock time or status |
| `playclock-update` | Play clock changes | Updated play clock time or status |
| `event-update` | Football events occur | New or updated football events |
| `statistics-update` | Statistics changes | Updated match statistics |
| `players-update` | Player match updates | Updated players list for the match |
| `ping` | Every 60 seconds | Heartbeat message for connection health check (match data endpoint only) |

##### Initial Load Message

```typescript
interface InitialLoadMessage {
  type: "initial-load";
  data: {
    match_id: number;
    id: number;
    match: MatchData;
    teams_data: {
      team_a: TeamData;
      team_b: TeamData;
    };
    match_data: {
      id: number;
      match_id: number;
      field_length?: number;
      game_status?: string;  // "in-progress", "stopped", "completed"
      score_team_a?: number;
      score_team_b?: number;
      timeout_team_a?: string;
      timeout_team_b?: string;
      qtr?: string;
      period_key?: string;
      ball_on?: number;
      down?: string;
      distance?: string;
    };
    scoreboard_data?: ScoreboardData;
    gameclock?: {
      id: number;
      match_id: number;
      gameclock: number;
      gameclock_max?: number;
      gameclock_status: string;  // "stopped", "running", "paused"
      gameclock_time_remaining?: number;
      started_at_ms?: number | null;
    };
    playclock?: {
      id: number;
      match_id: number;
      playclock: number;
      playclock_status: string;  // "stopped", "running", "paused"
      started_at_ms?: number | null;
    } | null;
    events: FootballEvent[];
    players: PlayerMatchData[];
    statistics: {
      team_a: {
        id: number;
        team_stats: TeamStats;
      };
      team_b: {
        id: number;
        team_stats: TeamStats;
      };
    };
    server_time_ms: number;
  };
}
```

When a sport preset disables playclock support (`has_playclock=false`), initial payload uses:

```json
{
  "playclock": null
}
```

##### Match Update Message

```typescript
interface MatchUpdateMessage {
  type: "match-update" | "message-update";
  match_id: number;
  match: MatchData;
  teams_data: {
    team_a: TeamData;
    team_b: TeamData;
  };
  match_data: {
    id: number;
    match_id: number;
    field_length?: number;
    game_status?: string;  // "in-progress", "stopped", "completed"
    score_team_a?: number;
    score_team_b?: number;
    timeout_team_a?: string;
    timeout_team_b?: string;
    qtr?: string;
    period_key?: string;
    ball_on?: number;
    down?: string;
    distance?: string;
  };
  scoreboard_data?: ScoreboardData;
}

interface TeamData {
  id: number;
  title: string;
  team_color: string;
  logo_url?: string;
}

interface ScoreboardData {
  id: number;
  match_id: number;
  is_qtr: boolean;
  period_mode: "qtr" | "period" | "half" | "set" | "inning" | "custom";
  period_count: number;
  period_labels_json?: string[] | null;
  is_time: boolean;
  is_playclock: boolean;
  is_downdistance: boolean;
  is_tournament_logo: boolean;
  team_a_game_color: string;
  team_b_game_color: string;
  team_a_game_title?: string;
  team_b_game_title?: string;
  // ... additional scoreboard fields
}
```

##### Gameclock Update Message

```typescript
interface GameclockUpdateMessage {
  type: "gameclock-update";
  match_id: number;
  gameclock: {
    id: number;
    match_id: number;
    gameclock: number;
    gameclock_max?: number;
    gameclock_status: string;  // "stopped", "running", "paused"
    gameclock_time_remaining?: number;
    started_at_ms?: number | null; // Unix timestamp (ms) when clock started
    server_time_ms?: number | null; // Server time (ms) when message sent
  };
}
```

##### Playclock Update Message

```typescript
interface PlayclockUpdateMessage {
  type: "playclock-update";
  match_id: number;
  playclock: {
    id: number;
    match_id: number;
    playclock?: number;
    playclock_status: string;  // "stopped", "running", "paused", "stopping"
    started_at_ms?: number | null;
  } | null;
  is_supported?: boolean; // false when sport preset has_playclock=false
  server_time_ms?: number;
}
```

##### Event Update Message

```typescript
interface EventUpdateMessage {
  type: "event-update";
  match_id: number;
  events: FootballEvent[];
}

interface FootballEvent {
  id: number;
  match_id: number;
  quarter: string;
  time_remaining: string;
  event_type: string;
  description?: string;
  player_id?: number;
  player?: {
    id: number;
    person: {
      first_name: string;
      last_name: string;
    };
  };
}
```

##### Ping Message (Heartbeat)

The server sends ping messages every 60 seconds to check connection health (match data endpoint only):

```typescript
interface PingMessage {
  type: "ping";
  timestamp: number;  // Unix timestamp in seconds
}
```

**Client should respond with pong:**

```typescript
interface PongMessage {
  type: "pong";
  timestamp: number;  // Echoed ping timestamp
}
```

**Important:**
- Client must respond to ping with pong to keep connection active
- Connections without pong response for 90 seconds are automatically cleaned up (match data endpoint only)
- Timestamp can be used to calculate round-trip latency

#### Client-Sent Messages

| Message Type | Direction | Description |
|--------------|-----------|-------------|
| `pong` | Client → Server | Response to server ping for connection health check |

#### PostgreSQL NOTIFY/LISTEN Mechanism

The backend uses PostgreSQL's `NOTIFY`/`LISTEN` mechanism for real-time updates:

**Channels:**
- `matchdata_change` - Match data updates
- `match_change` - Match information updates
- `scoreboard_change` - Scoreboard updates
- `playclock_change` - Play clock updates
- `gameclock_change` - Game clock updates
- `football_event_change` - Football event updates
- `player_match_change` - Player match updates

**How It Works:**
1. Database triggers send `NOTIFY` messages when relevant data changes
2. WebSocket manager listens for these notifications
3. Matched clients receive updates via their queues

#### Connection Lifecycle

```
Client                              Server
  |                                   |
  |----- CONNECT ---------------------->|  Client connects with match_id and client_id
  |                                   |
  |<---- message-update ------------|  Send full match context data
  |<---- playclock-update ----------|
  |<---- gameclock-update ---------|
  |                                   |
  |<---- ping (every 60s) ----------|  Heartbeat check (match data endpoint only)
  |----- pong ----------------------->|  Response to keep connection alive
  |                                   |
  |<---- match-update --------------|  When match data changes (via NOTIFY)
  |<---- gameclock-update ---------|  When game clock changes
  |<---- playclock-update ----------|  When play clock changes
  |<---- event-update -------------|  When football events change
  |                                   |
  |----- DISCONNECT ------------------->|  Client disconnects or closes connection
  |                                   |
```

#### Queue Management

Each client has:
- Individual queue per data type (match_data, playclock, gameclock, event)
- Match subscription mapping (match_id → list of client_ids)
- Automatic cleanup on disconnect

#### Timeout Configuration

- Queue get timeout: 60 seconds
- Ping interval: 60 seconds (server → client, match data endpoint only)
- Pong response: Client should respond with pong message
- Connection cleanup: 90 seconds without pong response
- Stale connection cleanup task runs every 60 seconds
- If no messages received within timeout, connection closes gracefully

---

### WebSocket Endpoint 2: Match Statistics

Real-time match statistics with conflict resolution for collaborative editing.

#### Connection

```typescript
const ws = new WebSocket('ws://localhost:9000/api/matches/ws/matches/{match_id}/stats');
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID to get stats for |

**Note:** Client ID is auto-generated by server (`id(websocket)`) for this endpoint.

#### Authentication

**Current Status:** No authentication required

#### Initial Data

```typescript
{
  "type": "full_stats_update",
  "match_id": 123,
  "stats": {
    "match_id": 123,
    "team_a": {
      "id": 1,
      "team_stats": {
        "id": 1,
        "offence_yards": 250,
        "pass_att": 20,
        "run_att": 30,
        "avg_yards_per_att": 5.0,
        "pass_yards": 150,
        "run_yards": 100,
        "lost_yards": 10,
        "flag_yards": -15,
        "third_down_attempts": 8,
        "third_down_conversions": 3,
        "fourth_down_attempts": 2,
        "fourth_down_conversions": 1,
        "first_down_gained": 15,
        "turnovers": 2
      },
      "offense_stats": {
        "456": {
          "id": 456,
          "pass_attempts": 10,
          "pass_received": 8,
          "pass_yards": 120,
          "pass_td": 1,
          "run_attempts": 5,
          "run_yards": 40,
          "run_avr": 8.0,
          "run_td": 0,
          "fumble": 0
        }
      },
      "qb_stats": {
        "789": {
          "id": 789,
          "passes": 15,
          "passes_completed": 10,
          "pass_yards": 150,
          "pass_td": 2,
          "pass_avr": 66.67,
          "run_attempts": 2,
          "run_yards": 10,
          "run_td": 0,
          "run_avr": 5.0,
          "fumble": 0,
          "interception": 1,
          "qb_rating": 85.5
        }
      },
      "defense_stats": {
        "101": {
          "id": 101,
          "tackles": 5,
          "assist_tackles": 3,
          "sacks": 1,
          "interceptions": 1,
          "fumble_recoveries": 1,
          "flags": 0
        }
      }
    },
    "team_b": {
      "id": 2,
      "team_stats": { /* same structure as team_a */ },
      "offense_stats": { /* same structure as team_a */ },
      "qb_stats": { /* same structure as team_a */ },
      "defense_stats": { /* same structure as team_a */ }
    }
  },
  "server_timestamp": "2026-01-21T17:30:00.123456"
}
```

#### Client-Sent Messages

##### Update Stats

Client can send stat updates with timestamp for conflict resolution.

```typescript
{
  "type": "stats_update",
  "match_id": 123,
  "stats": {
    "match_id": 123,
    "team_a": {
      "id": 1,
      "team_stats": {
        "offence_yards": 255
      }
    },
    "team_b": { /* unchanged */ }
  },
  "timestamp": "2026-01-21T17:33:00.123456"
}
```

**Conflict Resolution:**
- Server compares client `timestamp` with last write timestamp
- If client timestamp is newer → update accepted and broadcast to all other clients
- If server timestamp is newer → update rejected, client receives `stats_sync` with current data

#### Server-Sent Messages

##### 1. Stats Update

Broadcast when any client updates stats (or server-side changes occur).

```typescript
{
  "type": "stats_update",
  "match_id": 123,
  "stats": {
    "match_id": 123,
    "team_a": { /* full stats structure */ },
    "team_b": { /* full stats structure */ }
  },
  "server_timestamp": "2026-01-21T17:31:00.123456"
}
```

##### 2. Stats Sync (Conflict Resolution)

Sent when client's update is rejected due to conflict (server has newer data).

```typescript
{
  "type": "stats_sync",
  "match_id": 123,
  "stats": {
    "match_id": 123,
    "team_a": { /* current server stats */ },
    "team_b": { /* current server stats */ }
  },
  "server_timestamp": "2026-01-21T17:32:00.123456"
}
```

#### Stats Schema Details

##### Team Stats

```typescript
interface TeamStats {
  id: number;
  offence_yards: number;        // Total yards gained by offense
  pass_att: number;             // Total pass attempts
  run_att: number;              // Total run attempts
  avg_yards_per_att: number;    // Average yards per play (offence_yards / (pass_att + run_att))
  pass_yards: number;           // Total passing yards
  run_yards: number;            // Total rushing yards
  lost_yards: number;           // Total yards lost (sacks, fumbles, etc.)
  flag_yards: number;           // Total penalty yards (negative value)
  third_down_attempts: number;   // Third down attempts
  third_down_conversions: number; // Third down conversions
  fourth_down_attempts: number;   // Fourth down attempts
  fourth_down_conversions: number; // Fourth down conversions
  first_down_gained: number;     // First downs gained
  turnovers: number;             // Total turnovers (interceptions + lost fumbles)
}
```

##### Offense Stats

Keyed by `player_match_id` (player in match ID).

```typescript
interface OffenseStats {
  [playerMatchId: number]: {
    id: number;              // player_match_id
    pass_attempts: number;   // Pass attempts
    pass_received: number;   // Pass receptions
    pass_yards: number;      // Passing yards
    pass_td: number;         // Passing touchdowns
    run_attempts: number;    // Run attempts
    run_yards: number;      // Rushing yards
    run_avr: number;        // Average yards per rush
    run_td: number;         // Rushing touchdowns
    fumble: number;          // Fumbles
  };
}
```

##### QB Stats

Keyed by `player_match_id`.

```typescript
interface QBStats {
  [playerMatchId: number]: {
    id: number;              // player_match_id
    passes: number;          // Total passes attempted
    passes_completed: number; // Completed passes
    pass_yards: number;      // Passing yards
    pass_td: number;         // Passing touchdowns
    pass_avr: number;        // Pass completion percentage
    run_attempts: number;    // QB run attempts
    run_yards: number;      // QB rushing yards
    run_td: number;         // QB rushing touchdowns
    run_avr: number;        // QB average yards per rush
    fumble: number;          // QB fumbles
    interception: number;     // Interceptions thrown
    qb_rating: number;       // NFL-style QB rating
  };
}
```

**QB Rating Formula:**
```
QB Rating = (8.4 * pass_yards + 330 * pass_td + 100 * passes_completed - 200 * interception) / passes
```

##### Defense Stats

Keyed by `player_match_id`.

```typescript
interface DefenseStats {
  [playerMatchId: number]: {
    id: number;               // player_match_id
    tackles: number;          // Solo tackles
    assist_tackles: number;   // Assisted tackles
    sacks: number;            // Sacks
    interceptions: number;      // Interceptions
    fumble_recoveries: number; // Fumble recoveries
    flags: number;            // Penalties
  };
}
```

#### Connection Lifecycle

```
Client                              Server
  |                                   |
  |----- CONNECT ---------------------->|
  |                                   |
  |<---- full_stats_update ------------|  Send complete match statistics
  |                                   |
  |----- stats_update (optional) ---->|
  |<---- stats_sync (if conflict) -----|  Server rejects client's update
  |                                   |
  |<---- stats_update (broadcast) -----|  Broadcast to all connected clients
  |                                   |
  |----- stats_update --------------->|
  |                                   |
  |<---- stats_update (broadcast) -----|
  |                                   |
  |----- DISCONNECT ------------------->|
  |                                   |
```

#### Client Pooling

- Multiple clients can connect to the same match
- Updates are broadcast to all clients (except sender for direct updates)
- Server tracks last write timestamp per match for conflict resolution

---

### WebSocket Connection Examples

#### Example 1: Connect to Match Data WebSocket

```typescript
function connectToMatchDataWebSocket(matchId: number, clientId: string) {
  const ws = new WebSocket(
    `ws://localhost:9000/api/matches/ws/id/${matchId}/${clientId}`
  );

  ws.onopen = () => {
    console.log('Connected to match data WebSocket');
  };

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
      case 'message-update':
      case 'match-update':
        console.log('Match data updated:', message);
        // Update match display, teams, scoreboard
        break;
        
      case 'gameclock-update':
        console.log('Game clock updated:', message.gameclock);
        // Update game clock display
        break;
        
      case 'playclock-update':
        console.log('Play clock updated:', message.playclock);
        // Update play clock display
        break;
        
      case 'event-update':
        console.log('Events updated:', message.events);
        // Update event log or timeline
        break;
        
      default:
        console.warn('Unknown message type:', message.type);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = (event) => {
    console.log('WebSocket connection closed:', event.code, event.reason);
    // Implement reconnection logic here
  };
}

// Usage
connectToMatchDataWebSocket(123, 'client-abc-123');
```

#### Example 2: Connect to Match Stats WebSocket

```typescript
function connectToMatchStatsWebSocket(matchId: number) {
  const ws = new WebSocket(
    `ws://localhost:9000/api/matches/ws/matches/${matchId}/stats`
  );

  ws.onopen = () => {
    console.log('Connected to match stats WebSocket');
  };

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
      case 'full_stats_update':
        console.log('Initial stats loaded:', message.stats);
        // Initialize stats display with full data
        break;
        
      case 'stats_update':
        console.log('Stats updated:', message.stats);
        // Update stats display with new values
        break;
        
      case 'stats_sync':
        console.log('Stats synced from server:', message.stats);
        // Your update was rejected, apply server data
        break;
        
      default:
        console.warn('Unknown message type:', message.type);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = (event) => {
    console.log('WebSocket connection closed:', event.code, event.reason);
    // Implement reconnection logic here
  };
}

// Usage
connectToMatchStatsWebSocket(123);
```

#### Example 3: Update Stats via WebSocket

```typescript
function updateStats(ws: WebSocket, matchId: number, newStats: any) {
  if (ws.readyState === WebSocket.OPEN) {
    const message = {
      type: 'stats_update',
      match_id: matchId,
      stats: newStats,
      timestamp: new Date().toISOString()
    };
    
    ws.send(JSON.stringify(message));
    console.log('Stats update sent');
  } else {
    console.error('WebSocket not connected');
  }
}

// Usage
const ws = new WebSocket('ws://localhost:9000/api/matches/ws/matches/123/stats');

// When stats change (e.g., user edits stats)
function onStatsChange(updatedStats) {
  updateStats(ws, 123, updatedStats);
}
```

#### Example 4: Reconnection Strategy

```typescript
class ReconnectingWebSocket {
  constructor(url: string, reconnectInterval = 5000) {
    this.url = url;
    this.reconnectInterval = reconnectInterval;
    this.ws = null;
    this.shouldReconnect = true;
    
    this.connect();
  }

  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.onMessage?.(message);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      
      if (this.shouldReconnect) {
        console.log(`Reconnecting in ${this.reconnectInterval}ms...`);
        setTimeout(() => this.connect(), this.reconnectInterval);
      }
    };
  }

  close() {
    this.shouldReconnect = false;
    this.ws?.close();
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket not connected');
    }
  }
}

// Usage
const matchWs = new ReconnectingWebSocket(
  'ws://localhost:9000/api/matches/ws/id/123/client-abc-123'
);

matchWs.onMessage = (message) => {
  console.log('Received:', message);
};
```

---

## WebSocket Message Formats

### General Message Structure

All WebSocket messages follow this structure:

```typescript
interface WebSocketMessage {
  type: string;           // Message type identifier
  match_id: number;       // Match ID
  [key: string]: any;     // Additional type-specific fields
  server_timestamp?: string; // ISO 8601 timestamp (server-sent only)
  timestamp?: string;      // ISO 8601 timestamp (client-sent only)
}
```

### Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `full_stats_update` | Server → Client | Complete match statistics sent on connection |
| `stats_update` | Server → Client | Incremental stats update (broadcast) |
| `stats_update` | Client → Server | Stats update request with conflict resolution |
| `stats_sync` | Server → Client | Server rejects client update, sends current stats |
| `ping` | Server → Client | Heartbeat message sent every 60 seconds (match data endpoint only) |
| `pong` | Client → Server | Response to ping for connection health check (match data endpoint only) |

### Connection Lifecycle

```
Client                              Server
  |                                   |
  |----- CONNECT ---------------------->|
  |                                   |
  |<---- full_stats_update ------------|
  |                                   |
  |----- stats_update (optional) ---->|
  |<---- stats_sync (if conflict) -----|
  |                                   |
  |<---- stats_update (broadcast) -----|
  |<---- ping (every 60s) ----------|  Heartbeat check (match data endpoint only)
  |----- pong ----------------------->|  Response to keep connection alive
  |                                   |
  |----- stats_update --------------->|
  |                                   |
  |<---- stats_update (broadcast) -----|
  |                                   |
  |----- DISCONNECT ------------------->|
  |                                   |
```

### HTTP Endpoint: Match Statistics

#### GET /api/matches/id/{match_id}/stats/

Get complete match statistics for both teams without requiring a WebSocket connection.

**Endpoint:**
```
GET /api/matches/id/{match_id}/stats/
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match_id` | integer | Yes | Match ID |

**Response (200 OK):**

```json
{
  "match_id": 123,
  "team_a": {
    "id": 1,
    "team_stats": {
      "id": 1,
      "offence_yards": 250,
      "pass_att": 20,
      "run_att": 30,
      "avg_yards_per_att": 5.0,
      "pass_yards": 150,
      "run_yards": 100,
      "lost_yards": 10,
      "flag_yards": -15,
      "third_down_attempts": 8,
      "third_down_conversions": 3,
      "fourth_down_attempts": 2,
      "fourth_down_conversions": 1,
      "first_down_gained": 15,
      "turnovers": 2
    },
    "offense_stats": {
      "456": {
        "id": 456,
        "pass_attempts": 10,
        "pass_received": 8,
        "pass_yards": 120,
        "pass_td": 1,
        "run_attempts": 5,
        "run_yards": 40,
        "run_avr": 8.0,
        "run_td": 0,
        "fumble": 0
      }
    },
    "qb_stats": {
      "789": {
        "id": 789,
        "passes": 15,
        "passes_completed": 10,
        "pass_yards": 150,
        "pass_td": 2,
        "pass_avr": 66.67,
        "run_attempts": 2,
        "run_yards": 10,
        "run_td": 0,
        "run_avr": 5.0,
        "fumble": 0,
        "interception": 1,
        "qb_rating": 85.5
      }
    },
    "defense_stats": {
      "101": {
        "id": 101,
        "tackles": 5,
        "assist_tackles": 3,
        "sacks": 1,
        "interceptions": 1,
        "fumble_recoveries": 1,
        "flags": 0
      }
    }
  },
  "team_b": {
    "id": 2,
    "team_stats": { /* same structure as team_a */ },
    "offense_stats": { /* same structure as team_a */ },
    "qb_stats": { /* same structure as team_a */ },
    "defense_stats": { /* same structure as team_a */ }
  }
}
```

**Error Responses:**

- **404 Not Found** - Match doesn't exist
- **500 Internal Server Error** - Server error

---

## WebSocket Troubleshooting Guide

### Common Issues and Solutions

#### 1. Connection Refused

**Symptoms:**
- WebSocket connection fails immediately
- Error: `WebSocket connection to 'ws://localhost:9000/...' failed`

**Causes:**
- Backend server not running
- Wrong URL or port
- Firewall blocking WebSocket connections

**Solutions:**
```bash
# Check if backend is running
curl http://localhost:9000/health

# Start backend if not running
python src/runserver.py

# Check firewall settings
# Ensure WebSocket connections are allowed on port 9000
```

#### 2. Connection Timeout

**Symptoms:**
- Connection attempt hangs
- Timeout after several seconds

**Causes:**
- Network latency
- Database connection issues
- PostgreSQL NOTIFY/LISTENER setup problems

**Solutions:**
- Check database connectivity
- Verify PostgreSQL triggers are configured
- Check backend logs for database errors

#### 3. Frequent Disconnections

**Symptoms:**
- WebSocket connects but disconnects randomly
- Error: `Connection closed by remote host`

**Causes:**
- Network instability
- Database connection drops
- WebSocket manager issues
- Client timeout (60s queue timeout)
- Missing pong responses (stale connection cleanup after 90s)

**Solutions:**
- Implement exponential backoff reconnection strategy
- Check database connection stability
- Review server logs for errors
- Ensure client responds to ping messages with pong
- Check connection health logs for stale connection warnings

#### 4. No Messages Received

**Symptoms:**
- Connection established successfully
- No messages received from server
- Initial data messages not sent

**Causes:**
- PostgreSQL triggers not firing
- Match data doesn't exist
- Client not properly subscribed

**Solutions:**
```typescript
// Verify message handler is set up
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

// Check backend logs for NOTIFY messages
# Check PostgreSQL triggers
SELECT * FROM pg_trigger WHERE tgname LIKE '%websocket%';
```

#### 5. Message Parse Errors

**Symptoms:**
- `JSON.parse` errors
- Messages with unexpected structure
- Malformed data

**Causes:**
- Non-JSON messages
- Invalid message format
- Schema mismatches

**Solutions:**
```typescript
// Add error handling for JSON parsing
ws.onmessage = (event) => {
  try {
    const message = JSON.parse(event.data);
    handleMessage(message);
  } catch (error) {
    console.error('Failed to parse message:', event.data, error);
  }
};

// Validate message structure
function handleMessage(message: any) {
  if (!message.type || !message.match_id) {
    console.warn('Invalid message structure:', message);
    return;
  }
  // Process message
}
```

#### 6. Conflict Resolution Loops

**Symptoms:**
- Continuous `stats_sync` messages
- Stats never successfully update
- Infinite loop of updates

**Causes:**
- Multiple clients updating simultaneously
- Timestamp synchronization issues
- Incorrect timestamp handling

**Solutions:**
```typescript
// Implement debouncing for updates
let updatePending = false;

function sendStatsUpdate(stats: any) {
  if (updatePending) {
    console.log('Update already pending, skipping');
    return;
  }
  
  updatePending = true;
  ws.send(JSON.stringify({
    type: 'stats_update',
    match_id: matchId,
    stats: stats,
    timestamp: new Date().toISOString()
  }));
  
  // Reset after delay
  setTimeout(() => { updatePending = false; }, 1000);
}

// Handle stats_sync to update local state
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'stats_sync') {
    console.log('Applying server state:', message.stats);
    // Update local state with server data
    updatePending = false;
  }
};
```

### Debugging Tips

#### Enable WebSocket Debugging

```typescript
// Enable verbose logging
const ws = new WebSocket('ws://localhost:9000/api/matches/ws/id/123/client-abc');

ws.onopen = () => {
  console.log('[WebSocket] Connected');
};

ws.onmessage = (event) => {
  console.log('[WebSocket] Message:', event.data);
};

ws.onerror = (error) => {
  console.error('[WebSocket] Error:', error);
};

ws.onclose = (event) => {
  console.log('[WebSocket] Closed:', event.code, event.reason, event.wasClean);
};
```

#### Check Backend Logs

```bash
# WebSocket connection logs
tail -f logs/backend.log | grep WebSocket

# Match data handler logs
tail -f logs/backend.log | grep MatchDataWebSocket

# Stats handler logs
tail -f logs/backend.log | grep MatchStatsWebSocket

# Check for errors
tail -f logs/backend.log | grep -i error
```

#### Verify PostgreSQL Notifications

```sql
-- Check if NOTIFY messages are being sent
SELECT pg_notification_queue_usage();

-- Check active listeners
SELECT * FROM pg_listening_channels();

-- Manually trigger a notification for testing
NOTIFY matchdata_change, '{"match_id": 123}';
```

#### Monitor WebSocket Connections

```typescript
// Track connection state
class WebSocketMonitor {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private lastMessageTime = Date.now();

  connect(url: string) {
    this.ws = new WebSocket(url);
    
    this.ws.onopen = () => {
      console.log('[Monitor] Connected, attempts:', this.reconnectAttempts);
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      this.lastMessageTime = Date.now();
      const timeSinceLastMessage = Date.now() - this.lastMessageTime;
      
      if (timeSinceLastMessage > 60000) {  // 1 minute
        console.warn('[Monitor] No messages for 1 minute');
      }
    };

    this.ws.onerror = (error) => {
      console.error('[Monitor] Error, attempts:', this.reconnectAttempts);
      this.reconnectAttempts++;
    };

    this.ws.onclose = (event) => {
      console.log('[Monitor] Closed, code:', event.code);
      if (event.code !== 1000) {
        // Abnormal close, attempt reconnect
        this.reconnectAttempts++;
        setTimeout(() => this.connect(url), Math.min(1000 * this.reconnectAttempts, 30000));
      }
    };
  }
}
```

### Performance Optimization

#### 1. Batch Updates

```typescript
// Collect multiple updates before sending
const updateQueue: any[] = [];
let flushScheduled = false;

function queueUpdate(update: any) {
  updateQueue.push(update);
  
  if (!flushScheduled) {
    flushScheduled = true;
    requestAnimationFrame(flushUpdates);
  }
}

function flushUpdates() {
  if (updateQueue.length === 0) {
    flushScheduled = false;
    return;
  }
  
  // Apply all updates at once
  applyUpdates(updateQueue);
  updateQueue.length = 0;
  flushScheduled = false;
}
```

#### 2. Use Server-Sent Caching

```typescript
// Cache initial data to avoid redundant requests
let cachedStats: any = null;

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'full_stats_update') {
    cachedStats = message.stats;
    updateDisplay(message.stats);
  } else if (message.type === 'stats_update') {
    if (cachedStats) {
      // Merge update with cached data
      const merged = mergeStats(cachedStats, message.stats);
      cachedStats = merged;
      updateDisplay(merged);
    }
  }
};
```

#### 3. Debounce Updates

```typescript
// Debounce rapid updates to prevent UI thrashing
let debounceTimer: any = null;

function debouncedUpdate(update: any) {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    applyUpdate(update);
  }, 100);  // 100ms debounce
}
```

### Testing WebSocket Connections

#### Test Match Data WebSocket

```javascript
// Simple test script
const testWs = new WebSocket('ws://localhost:9000/api/matches/ws/id/123/test-client');

let messageCount = 0;
let startTime = Date.now();

testWs.onopen = () => {
  console.log('✅ WebSocket connected');
};

testWs.onmessage = (event) => {
  messageCount++;
  const elapsed = (Date.now() - startTime) / 1000;
  console.log(`📨 Message #${messageCount} (${elapsed.toFixed(2)}s)`);
  console.log('Data:', JSON.parse(event.data));
};

testWs.onerror = (error) => {
  console.error('❌ WebSocket error:', error);
};

testWs.onclose = (event) => {
  console.log(`🔌 WebSocket closed after ${(Date.now() - startTime) / 1000}s`);
  console.log('Messages received:', messageCount);
};

// Auto-close after 30 seconds
setTimeout(() => {
  testWs.close();
}, 30000);
```

#### Test Match Stats WebSocket

```javascript
const testStatsWs = new WebSocket('ws://localhost:9000/api/matches/ws/matches/123/stats');

testStatsWs.onopen = () => {
  console.log('✅ Stats WebSocket connected');
};

testStatsWs.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('📊 Message type:', message.type);
  
  if (message.type === 'full_stats_update') {
    console.log('📦 Full stats loaded');
  } else if (message.type === 'stats_update') {
    console.log('🔄 Stats updated');
  } else if (message.type === 'stats_sync') {
    console.log('🔒 Stats synced (conflict)');
  }
};

testStatsWs.onerror = (error) => {
  console.error('❌ Stats WebSocket error:', error);
};

testStatsWs.onclose = (event) => {
  console.log('🔌 Stats WebSocket closed');
};
```

### Security Considerations

#### Current Status

WebSocket endpoints currently **do not require authentication**. This is acceptable for:

- Public match data viewing
- Real-time scoreboards
- Public statistics

#### Future Authentication

When authentication is implemented, use:

```typescript
// Option 1: Query parameter (recommended)
const token = getAuthToken();
const ws = new WebSocket(
  `ws://localhost:9000/api/matches/ws/id/123/client-abc?token=${token}`
);

// Option 2: Subprotocol
const ws = new WebSocket('ws://localhost:9000/api/matches/ws/id/123/client-abc', ['statsboard-auth']);
```

#### Data Validation

Always validate WebSocket messages on client side:

```typescript
function validateMessage(message: any): boolean {
  // Check required fields
  if (!message || typeof message !== 'object') {
    return false;
  }
  
  if (!message.type || typeof message.type !== 'string') {
    return false;
  }
  
  if (!message.match_id || typeof message.match_id !== 'number') {
    return false;
  }
  
  // Type-specific validation
  switch (message.type) {
    case 'gameclock-update':
      return !!message.gameclock && typeof message.gameclock.gameclock === 'number';
      
    case 'playclock-update':
      return !!message.playclock && typeof message.playclock.playclock === 'number';
      
    case 'stats_update':
      return !!message.stats && !!message.timestamp;
      
    default:
      return true;
  }
}

ws.onmessage = (event) => {
  try {
    const message = JSON.parse(event.data);
    
    if (!validateMessage(message)) {
      console.warn('Invalid message received:', message);
      return;
    }
    
    handleMessage(message);
  } catch (error) {
    console.error('Message validation error:', error);
  }
};
```

### Best Practices

1. **Always handle connection states:** Monitor `onopen`, `onmessage`, `onerror`, `onclose`
2. **Implement exponential backoff:** Don't spam reconnection attempts
3. **Validate messages:** Never trust WebSocket data without validation
4. **Cache data:** Store initial data and apply incremental updates
5. **Debounce updates:** Prevent UI thrashing from rapid updates
6. **Log everything:** Enable verbose logging for debugging
7. **Test with curl:** Verify server is running before connecting
8. **Monitor performance:** Track message frequency and connection stability
9. **Handle errors gracefully:** Show user-friendly error messages
10. **Clean up on disconnect:** Remove event listeners and timers

---
