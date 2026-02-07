# WebSocket Data Flow Documentation

## Overview

This document is now an index. See the split WebSocket docs:

- `docs/websockets/index.md`

## Architecture Diagram

```
┌─────────────────┐
│  Database (PG)  │
│  - Tables       │
│  - Triggers     │
└────────┬────────┘
         │ pg_notify()
         │
         ▼
 ┌─────────────────────────────────────────┐
  │  MatchDataWebSocketManager            │
  │  - Listeners (asyncpg)             │
  │  - match_data_listener (CUSTOM)      │
  │  - gameclock_listener (_base)        │
  │  - playclock_listener (_base)        │
  │  - event_listener (CUSTOM)           │
  │  - players_update_listener (CUSTOM)  │
 └────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  ConnectionManager                    │
│  - Queues per client                │
│  - Match subscriptions              │
│  - send_to_all()                   │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  MatchWebSocketHandler               │
│  - process_data_websocket()         │
│  - process_match_data() (fetch)     │
│  - process_gameclock_data() (fetch) │
│  - process_playclock_data() (fetch) │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  WebSocket (FastAPI)               │
│  - /ws/id/{match_id}/{client_id}/  │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Frontend WebSocket Service         │
│  - WebSocketService                 │
│  - Signals (matchData, gameClock)   │
│  - Effects (merge updates)         │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Components                         │
│  - ScoreboardViewComponent          │
│  - Effects update UI                │
└─────────────────────────────────────────┘
```

## Message Types

### 1. Initial Load (`initial-load`)

**When sent:** On successful WebSocket connection

**Source:** `MatchWebSocketHandler.send_initial_data()`

**Backend flow:**
1. WebSocket connection accepted
2. Fetch all match-related data in parallel:
    - `fetch_with_scoreboard_data(match_id)` → match, teams, matchdata, scoreboard, players, events, sponsors_data, sponsor_line sponsors
   - `fetch_gameclock(match_id)` → gameclock
   - `fetch_playclock(match_id)` → playclock
   - `fetch_event(match_id)` → events (redundant with scoreboard fetch)
   - `fetch_stats(match_id)` → match statistics
3. Combine into single message

**Message structure:**
```json
{
  "type": "initial-load",
  "data": {
    "match_id": 67,
    "id": 67,
    "status_code": 200,
    "match": {
      "id": 67,
      "team_a_id": 1,
      "team_b_id": 2,
      "tournament_id": 5,
      "scheduled_at": "2026-01-27T10:00:00",
      "sponsor_line": {
        "id": 3,
        "title": "Match Sponsors",
        "sponsors": [
          {
            "sponsor": {
              "id": 1,
              "title": "Acme Corp",
              "logo_url": "/static/uploads/sponsors/logos/acme.png",
              "scale_logo": 1.5
            },
            "position": 1
          },
          {
            "sponsor": {
              "id": 2,
              "title": "Beta Industries",
              "logo_url": "/static/uploads/sponsors/logos/beta.png",
              "scale_logo": 1.0
            },
            "position": 2
          }
        ]
      },
      "tournament": {
        "id": 5,
        "title": "Championship Tournament",
        "sponsor_line": {
          "id": 4,
          "title": "Tournament Sponsors",
          "sponsors": [
            {
              "sponsor": {
                "id": 3,
                "title": "Global Sports",
                "logo_url": "/static/uploads/sponsors/logos/global.png",
                "scale_logo": 1.0
              },
              "position": 1
            }
          ]
        }
      }
    },
    "teams_data": {
      "team_a": {
        "id": 1,
        "title": "Team A",
        "team_color": "#FF0000"
      },
      "team_b": {
        "id": 2,
        "title": "Team B",
        "team_color": "#0000FF"
      }
    },
    "match_data": {
      "id": 67,
      "match_id": 67,
      "score_team_a": 22,
      "score_team_b": 40,
      "qtr": "3rd",
      "down": "2nd",
      "distance": "Inches",
      "ball_on": 20,
      "game_status": "in-progress",
      "timeout_team_a": "oo●",
      "timeout_team_b": "oo●",
      "field_length": 92
    },
    "scoreboard_data": {
      "id": 67,
      "match_id": 67,
      "is_main_sponsor": false,
      "show_team_names": true
    },
    "sponsors_data": {
      "match": {
        "main_sponsor": null,
        "sponsor_line": {
          "id": 3,
          "title": "Match Sponsors",
          "is_visible": true,
          "sponsors": [
            {
              "position": 1,
              "sponsor": {
                "id": 1,
                "title": "Acme Corp",
                "logo_url": "/static/uploads/sponsors/logos/acme.png",
                "scale_logo": 1.5
              }
            },
            {
              "position": 2,
              "sponsor": {
                "id": 2,
                "title": "Beta Industries",
                "logo_url": "/static/uploads/sponsors/logos/beta.png",
                "scale_logo": 1.0
              }
            }
          ]
        }
      },
      "tournament": {
        "main_sponsor": null,
        "sponsor_line": {
          "id": 4,
          "title": "Tournament Sponsors",
          "is_visible": true,
          "sponsors": [
            {
              "position": 1,
              "sponsor": {
                "id": 3,
                "title": "Global Sports",
                "logo_url": "/static/uploads/sponsors/logos/global.png",
                "scale_logo": 1.0
              }
            }
          ]
        }
      }
    },
    "players": [
      {
        "id": 100,
        "player_id": 50,
        "match_id": 67,
        "team_id": 1,
        "team": {"id": 1, "title": "Team A"},
        "player": {"id": 50, "name": "John Doe"}
      }
    ],
    "events": [],
    "gameclock": {
      "id": 67,
      "match_id": 67,
      "gameclock": 720,
      "gameclock_status": "running",
      "updated_at": "2026-01-27T16:00:00"
    },
    "playclock": {
      "id": 67,
      "match_id": 67,
      "playclock": 40,
      "playclock_status": "stopped",
      "updated_at": "2026-01-27T16:00:00"
    },
    "statistics": {
      "match_id": 67,
      "team_a": {
        "id": 1,
        "title": "Team A",
        "touchdowns": 3,
        "field_goals": 1
      },
      "team_b": {
        "id": 2,
        "title": "Team B",
        "touchdowns": 5,
        "field_goals": 2
      }
    },
    "server_time_ms": 1737974401234
  }
}
```

**Message size:** ~5-10KB (full data)

**Frontend handling:**
```typescript
// WebSocketService.handleMessage() handles 'initial-load' type
if (messageType === 'initial-load') {
  const data = message['data'];
  
  // Set main match data signal (includes all nested fields)
  this.matchData.set({
    match_data: data['match_data'],
    match: data['match'],
    teams_data: data['teams_data'],
    scoreboard_data: data['scoreboard_data'],
    sponsors_data: data['sponsors_data'],
    players: data['players'] || [],
    events: data['events'] || [],
    gameclock: data['gameclock'],
    playclock: data['playclock'],
    statistics: data['statistics']
  });
  
  // Also set clock signals separately for predictor sync
  if (data['gameclock']) {
    this.gameClock.set(this.mergeGameClock(data['gameclock']));
  }
  if (data['playclock']) {
    this.playClock.set(this.mergePlayClock(data['playclock']));
  }
}
```

---

### 2. Match Update (`match-update`)

**When sent:** When `matchdata` or `scoreboard` tables change

**Source:** Database trigger → `MatchDataWebSocketManager.match_data_listener()`

**Backend flow:**
1. Database trigger fires: `notify_matchdata_change()`
2. Sends pg_notify with payload:
   ```json
   {
     "table": "matchdata",
     "operation": "UPDATE",
     "new_id": 67,
     "old_id": 67,
     "match_id": 67,
     "data": {
       "id": 67,
       "match_id": 67,
       "score_team_a": 22,
       "score_team_b": 40,
       // ... ALL fields (row_to_json(NEW))
     }
   }
   ```
3. `match_data_listener()` receives notification
4. **Invalidates cache:** `cache_service.invalidate_match_data(match_id)`
5. **Smart payload selection:**
   - If trigger payload contains 'data' field (UPDATE/INSERT): Sends trigger data directly
   - If trigger payload has no 'data' (DELETE/legacy): Falls back to `fetch_with_scoreboard_data()`
6. **Sends:**
   ```json
   {
     "type": "match-update",
     "data": {
       "id": 67,
       "match_id": 67,
       "score_team_a": 22,
       "score_team_b": 40
       // ... only changed row fields
     }
   }
   ```

**Important:** This is **partial data** (changed row only) for UPDATE/INSERT operations, reducing network payload from ~3-8KB to ~200-400B for score updates. Full data fetch only occurs when trigger data is unavailable (DELETE operations or legacy triggers).

**Message structure (UPDATE/INSERT with trigger data):**
```json
{
  "type": "match-update",
  "data": {
    "id": 67,
    "match_id": 67,
    "score_team_a": 22,
    "score_team_b": 40,
    "qtr": "3rd",
    "down": "2nd",
    "distance": "Inches",
    "ball_on": 20,
    "game_status": "in-progress",
    "timeout_team_a": "oo●",
    "timeout_team_b": "oo●",
    "field_length": 92
  }
}
```

**Message size:** ~200-400B (partial data - changed row only)

**Channel-specific behavior:**

#### Scoreboard Update (`scoreboard_change` channel)

When the `scoreboard` table changes (display settings, team settings, scale settings), the backend wraps the data differently:

**Backend flow:**
1. Database trigger fires: `notify_scoreboard_change()`
2. Sends pg_notify with payload containing `row_to_json(NEW)` scoreboard data
3. `match_data_listener()` receives notification with channel `scoreboard_change`
4. **Wraps data:** Backend wraps scoreboard data under `scoreboard_data` key
5. **Sends:**
   ```json
   {
     "type": "match-update",
     "data": {
       "scoreboard_data": {
         "id": 67,
         "match_id": 67,
         "is_qtr": true,
         "is_time": true,
         "is_playclock": true,
         "is_downdistance": true,
         "is_tournament_logo": true,
         "is_main_sponsor": true,
         "use_team_a_game_color": false,
         "use_team_b_game_color": false,
         "team_a_game_color": "#FF0000",
         "team_b_game_color": "#0000FF",
         // ... other scoreboard fields
       }
     }
   }
   ```

**Frontend handling:**
```typescript
// WebSocketService.handleMessage() extracts scoreboard_data
const scoreboardData = data['scoreboard_data'];
if (scoreboardData) {
  this.scoreboardPartial.set(scoreboardData);
}
```

#### Matchdata Update (`matchdata_change` channel)

When the `matchdata` table changes (scores, game state, play clock info), the backend sends raw data:

**Backend flow:**
1. Database trigger fires: `notify_matchdata_change()`
2. Sends pg_notify with payload containing `row_to_json(NEW)` matchdata data
3. `match_data_listener()` receives notification with channel `matchdata_change`
4. **Sends raw data:** Backend sends matchdata fields directly (frontend detects by field presence)
5. **Sends:**
   ```json
   {
     "type": "match-update",
     "data": {
       "id": 67,
       "match_id": 67,
       "score_team_a": 22,
       "score_team_b": 40,
       "qtr": "3rd",
       "down": "2nd",
       "distance": "Inches",
       "ball_on": 20,
       "game_status": "in-progress",
       // ... other matchdata fields
     }
   }
   ```

**Frontend handling:**
```typescript
// WebSocketService.handleMessage() detects matchdata fields
const hasMatchDataFields = [
  'score_team_a', 'score_team_b', 'qtr', 'down', 'distance',
  'ball_on', 'timeout_team_a', 'timeout_team_b', 'field_length', 'game_status'
].some(field => field in data);

if (hasMatchDataFields) {
  this.matchDataPartial.set(data);
}
```

**Important:** This is **partial data** (changed row only) for UPDATE/INSERT operations, reducing network payload from ~3-8KB to ~200-400B for score updates. Full data fetch only occurs when trigger data is unavailable (DELETE operations or legacy triggers).

**Message structure (UPDATE/INSERT with trigger data):**
```json
{
  "type": "match-update",
  "data": {
    "match_id": 67,
    "id": 67,
    "status_code": 200,
    "match": {
      "id": 67,
      "team_a_id": 1,
      "team_b_id": 2,
      "tournament_id": 5,
      "scheduled_at": "2026-01-27T10:00:00",
      "sponsor_line": {
        "id": 3,
        "title": "Match Sponsors",
        "sponsors": [
          {
            "sponsor": {
              "id": 1,
              "title": "Acme Corp",
              "logo_url": "/static/uploads/sponsors/logos/acme.png",
              "scale_logo": 1.5
            },
            "position": 1
          }
        ]
      },
      "tournament": {
        "id": 5,
        "title": "Championship Tournament",
        "sponsor_line": {
          "id": 4,
          "title": "Tournament Sponsors",
          "sponsors": [
            {
              "sponsor": {
                "id": 3,
                "title": "Global Sports",
                "logo_url": "/static/uploads/sponsors/logos/global.png",
                "scale_logo": 1.0
              },
              "position": 1
            }
          ]
        }
      }
    },
    "teams_data": {
      "team_a": {
        "id": 1,
        "title": "Team A",
        "team_color": "#FF0000"
      },
      "team_b": {
        "id": 2,
        "title": "Team B",
        "team_color": "#0000FF"
      }
    },
    "match_data": {
      "id": 67,
      "match_id": 67,
      "score_team_a": 22,
      "score_team_b": 40,
      "qtr": "3rd",
      "down": "2nd",
      "distance": "Inches",
      "ball_on": 20,
      "game_status": "in-progress",
      "timeout_team_a": "oo●",
      "timeout_team_b": "oo●",
      "field_length": 92
    },
    "scoreboard_data": {
      "id": 67,
      "match_id": 67,
      "is_main_sponsor": false,
      "show_team_names": true
    },
    "players": [
      {
        "id": 100,
        "player_id": 50,
        "match_id": 67,
        "team_id": 1,
        "team": {"id": 1, "title": "Team A"},
        "player": {"id": 50, "name": "John Doe"}
      }
    ],
    "events": []
  }
}
```

**Message size (fallback):** ~3-8KB (full data with all relations)

**Frontend handling:**
```typescript
// WebSocketService.handleMessage() handles 'match-update' type
if (messageType === 'match-update') {
  const data = message['data'];
  
  // Set partial update signals
  if (data['match_data']) {
    this.matchDataPartial.set(data['match_data']);
    this.lastMatchDataUpdate.set(Date.now());
  }
  
  if (data['scoreboard_data']) {
    this.scoreboardPartial.set(data['scoreboard_data']);
  }
  
  if (data['match']) {
    this.matchPartial.set(data['match']);
    this.lastMatchUpdate.set(Date.now());
  }
  
  if (data['teams_data']) {
    this.teamsPartial.set(data['teams_data']);
    this.lastTeamsUpdate.set(Date.now());
  }
  
  if (data['players']) {
    this.playersPartial.set(data['players']);
    this.lastPlayersUpdate.set(Date.now());
  }
  
  if (data['events']) {
    this.eventsPartial.set(data['events']);
    this.lastEventsUpdate.set(Date.now());
  }
  
  // Keep clock updates for predictor sync
  if (data['gameclock']) {
    this.gameClock.set(this.mergeGameClock(data['gameclock']));
  }
  if (data['playclock']) {
    this.playClock.set(this.mergePlayClock(data['playclock']));
  }
}
```

**Component effects (ScoreboardViewComponent):**
```typescript
// Each partial signal triggers its own effect
private wsMatchDataPartialEffect = effect(() => {
  const partial = this.wsService.matchDataPartial();
  if (!partial) return;
  
  const current = untracked(() => this.data());
  if (!current) return;
  
  // Merge only match_data field
  this.data.set({
    ...current,
    match_data: partial,
  });
});

private wsScoreboardPartialEffect = effect(() => {
  const partial = this.wsService.scoreboardPartial();
  if (!partial) return;
  
  const current = untracked(() => this.data());
  if (!current) return;
  
  // Merge only scoreboard field
  this.data.set({
    ...current,
    scoreboard: partial,
  });
});

// Similar effects for matchPartial, teamsPartial, playersPartial, eventsPartial
```

---

### 3. Gameclock Update (`gameclock-update`)

**When sent:** When `gameclock` table changes

**Source:** Database trigger → `MatchDataWebSocketManager.gameclock_listener()`

**Backend flow:**
1. Database trigger fires: `notify_gameclock_change()`
2. Sends pg_notify with payload (from trigger)
3. `gameclock_listener()` receives via `_base_listener()`
4. **Invalidates cache:** `cache_service.invalidate_gameclock(match_id)`
5. **Sends directly:** Forwards trigger payload (doesn't fetch fresh data)

**Message structure:**
```json
{
  "type": "gameclock-update",
  "match_id": 67,
  "gameclock": {
    "id": 67,
    "match_id": 67,
    "gameclock": 719,
    "gameclock_status": "running",
    "updated_at": "2026-01-27T16:00:01"
  }
}
```

**Message size:** ~200-400B

**Frontend handling:**
```typescript
if (messageType === 'gameclock-update') {
  const gameclock = message['gameclock'];
  
  // Merge with current state (version/timestamp comparison)
  this.gameClock.set(this.mergeGameClock(gameclock));
}
```

---

### 4. Playclock Update (`playclock-update`)

**When sent:** When `playclock` table changes

**Source:** Database trigger → `MatchDataWebSocketManager.playclock_listener()`

**Backend flow:**
1. Database trigger fires: `notify_playclock_change()`
2. Sends pg_notify with payload (from trigger)
3. `playclock_listener()` receives via `_base_listener()`
4. **Invalidates cache:** `cache_service.invalidate_playclock(match_id)`
5. **Sends directly:** Forwards trigger payload (doesn't fetch fresh data)

**Message structure:**
```json
{
  "type": "playclock-update",
  "match_id": 67,
  "playclock": {
    "id": 67,
    "match_id": 67,
    "playclock": 39,
    "playclock_status": "running",
    "updated_at": "2026-01-27T16:00:01"
  }
}
```

**Message size:** ~200-400B

**Frontend handling:**
```typescript
if (messageType === 'playclock-update') {
  const playclock = message['playclock'];
  
  // Merge with current state (version/timestamp comparison)
  this.playClock.set(this.mergePlayClock(playclock));
}
```

---

### 5. Event Update (`event-update`)

**When sent:** When `football_event` table changes

**Source:** Database trigger → `MatchDataWebSocketManager.event_listener()`

 **Backend flow:**
1. Database trigger fires: `notify_football_event_change()`
2. Sends pg_notify with payload:
    ```json
    {
      "table": "football_event",
      "operation": "INSERT/UPDATE/DELETE",
      "match_id": 67
    }
    ```
3. `event_listener()` receives notification
4. **Invalidates cache:** `cache_service.invalidate_event_data(match_id)`
5. **Fetches full events:** `FootballEventServiceDB.get_events_with_players(match_id)`
6. **Sends event-update:**
    ```json
    {
      "type": "event-update",
      "match_id": 67,
      "events": [
        {
          "id": 500,
          "match_id": 67,
          "event_number": 42,
          "play_type": "touchdown",
          "event_qtr": "3rd",
          "offense_team": 2,
          "qb": {
            "id": 100,
            "player_id": 50,
            "player": {
              "first_name": "John",
              "second_name": "Doe",
              "person_photo_url": "http://example.com/photo.jpg"
            },
            "position": {"id": 1, "name": "QB"},
            "team": {
              "id": 2,
              "name": "Team B",
              "logo_url": "http://example.com/logo.png"
            }
          }
        }
      ]
    }
    ```
7. **Invalidates stats:** `cache_service.invalidate_stats(match_id)` (events affect stats)
8. **Sends statistics-update:** Via `_base_listener()` to notify clients of stats change

**Message structure (event-update):**
```json
{
  "type": "event-update",
  "match_id": 67,
  "events": [
    {
      "id": 500,
      "match_id": 67,
      "event_number": 42,
      "event_qtr": "3rd",
      "ball_on": 20,
      "ball_moved_to": 25,
      "distance_on_offence": 5,
      "offense_team": 2,
      "event_qb": 100,
      "event_down": "1st",
      "event_distance": 10,
      "play_type": "touchdown",
      "play_result": "touchdown",
      "qb": {
        "id": 100,
        "player_id": 50,
        "player": {
          "first_name": "John",
          "second_name": "Doe",
          "person_photo_url": "http://example.com/photo.jpg"
        },
        "position": {
          "id": 1,
          "name": "QB"
        },
        "team": {
          "id": 2,
          "name": "Team B",
          "logo_url": "http://example.com/logo.png"
        }
      },
      "score_player": {
        "id": 101,
        "player_id": 51,
        "player": {
          "first_name": "Jane",
          "second_name": "Smith"
        },
        "team": {
          "id": 2,
          "name": "Team B"
        }
      }
    }
  ]
}
```

**Important:** Events are sent at the **top level** of the message (not nested in `data`), matching frontend expectations. Events include full player relationships with person, position, and team data.

**Message size:** ~1-5KB (depends on number of events and player relationships)

**Frontend handling:**
```typescript
if (messageType === 'event-update') {
  const events = message['events'];
  
  this.events.set(events);
  this.lastEventUpdate.set(Date.now());
}
```

---

### 6. Statistics Update (`statistics-update`)

**When sent:** When `football_event` table changes (same as event-update)

**Source:** Database trigger → `MatchDataWebSocketManager.event_listener()`

**Backend flow:** Same as event-update, sends second message

**Message structure:**
```json
{
  "type": "statistics-update",
  "match_id": 67,
  "statistics": {
    "match_id": 67,
    "team_a": {
      "id": 1,
      "title": "Team A",
      "touchdowns": 3,
      "field_goals": 1,
      "total_points": 22
    },
    "team_b": {
      "id": 2,
      "title": "Team B",
      "touchdowns": 5,
      "field_goals": 2,
      "total_points": 40
    }
  }
}
```

**Message size:** ~1-2KB

**Frontend handling:**
```typescript
if (messageType === 'statistics-update') {
  const stats = message['statistics'];
  
  this.statistics.set(stats);
  this.lastStatsUpdate.set(Date.now());
}
```

---

### 7. Players Update (`players-update`)

**When sent:** When `player_match` table changes

**Source:** Database trigger → `MatchDataWebSocketManager.players_update_listener()`

**Backend flow:**
1. Database trigger fires: `notify_player_match_change()`
2. Sends pg_notify with payload:
   ```json
   {
     "table": "player_match",
     "operation": "UPDATE",
     "match_id": 67
   }
   ```
3. `players_update_listener()` receives notification
4. **Invalidates cache:** `cache_service.invalidate_players(match_id)`
5. **Fetches players:** `get_players_with_full_data_optimized(match_id)`
6. **Sends:**
   ```json
   {
     "type": "players-update",
     "data": {
       "match_id": 67,
       "players": [
         {
           "id": 100,
           "player_id": 50,
           "match_id": 67,
           "team_id": 1,
           "team": {"id": 1, "title": "Team A"},
           "player": {"id": 50, "name": "John Doe"}
         }
       ]
     }
   }
   ```

**Message size:** ~1-5KB (depends on number of players)

**Frontend handling:**
```typescript
if (messageType === 'players-update') {
  const data = message['data'];
  
  if (data['players']) {
    this.players.set(data['players']);
    this.lastPlayersUpdate.set(Date.now());
  }
}
```

---

## Special Cases

### Fallback on Data Fetch Failure

If `fetch_with_scoreboard_data()` fails (returns None or missing 'data' key), the listener sends partial data from the trigger payload:

```python
# Fallback in match_data_listener
else:
    self.logger.warning(
        f"Failed to fetch full match data for match {match_id}, sending partial data"
    )
    message = {"type": "match-update", "data": trigger_data.get("data", {})}
    await connection_manager.send_to_all(message, match_id=match_id)
```

This ensures at least some data reaches the frontend even if the full fetch fails.

---

### Error Handling

All listeners include comprehensive error handling:

```python
try:
    trigger_data = json.loads(payload.strip())
    match_id = trigger_data["match_id"]
    # ... processing logic
except json.JSONDecodeError as e:
    self.logger.error(f"JSON decode error in match_data_listener: {str(e)}", exc_info=True)
except Exception as e:
    self.logger.error(f"Error in match_data_listener: {str(e)}", exc_info=True)
```

---

## Cache Invalidation Strategy

The cache service is invalidated before sending messages to ensure fresh data:

| Message Type | Cache Invalidation |
|--------------|-------------------|
| `match-update` | `invalidate_match_data(match_id)` |
| `gameclock-update` | `invalidate_gameclock(match_id)` |
| `playclock-update` | `invalidate_playclock(match_id)` |
| `event-update` | `invalidate_event_data(match_id)` |
| `statistics-update` | `invalidate_stats(match_id)` |
| `players-update` | `invalidate_players(match_id)` |

For `match-update`, the full data is **fetched fresh** after cache invalidation, ensuring consistency.

---

## Client Queue System

Each WebSocket client has its own queue:

```python
# ConnectionManager
self.queues: dict[str, asyncio.Queue] = {}
self.match_subscriptions: dict[str | int, list[str]] = {}
self.last_activity: dict[str, float] = {}
```

**Flow:**
1. Client connects with `client_id` and `match_id`
2. Queue created: `queues[client_id] = asyncio.Queue()`
3. Subscription added: `match_subscriptions[match_id].append(client_id)`
4. Activity tracking: `last_activity[client_id] = time.time()`
5. When message arrives, sent to all queues for that `match_id`
6. `process_data_websocket()` reads from queue and sends to WebSocket
7. Activity updated on each message: `update_client_activity(client_id)`

**Benefits:**
- Decouples message generation from message sending
- Prevents blocking on slow WebSocket connections
- Handles multiple clients per match
- Enables automatic cleanup of stale connections

---

## Connection Lifecycle Management

### Automatic Stale Connection Cleanup

The system includes automatic cleanup of inactive WebSocket connections to prevent resource leaks:

```python
# ConnectionManager method
async def cleanup_stale_connections(self, timeout_seconds: float = 90.0):
    now = time.time()
    stale_clients = [
        client_id
        for client_id, last_seen in self.last_activity.items()
        if now - last_seen > timeout_seconds
    ]
    for client_id in stale_clients:
        self.logger.warning(
            f"Cleaning up stale connection for client {client_id} "
            f"(inactive for {now - self.last_activity[client_id]:.1f}s)"
        )
        await self.disconnect(client_id)
```

**Background Task:**
- Runs every 60 seconds
- Checks all client activity timestamps
- Removes connections inactive for >90 seconds
- Safely disconnects stale clients and cleans up resources

**Benefits:**
- Prevents connection leaks
- Frees resources for active clients
- Handles network interruptions gracefully
- Maintains accurate active connection count

### Disconnect Handling

The system properly handles disconnected WebSocket clients:

```python
# In receive_messages loop
if websocket.application_state != WebSocketState.CONNECTED:
    websocket_logger.warning(
        f"WebSocket disconnected (state: {websocket.application_state}), "
        f"ending processing loop after timeout"
    )
    break
```

**Behavior:**
- Detects disconnected WebSocket state during queue operations
- Breaks processing loop when client disconnects
- Logs disconnection events for debugging
- Ensures cleanup happens properly on disconnect

---

## Testing the Flow

### Verify Full Data Chain

```bash
# 1. Start backend with debug logging
python -m uvicorn src.main:app --reload --log-level debug

# 2. Connect frontend to match
# Open: http://localhost:4200/scoreboard/view/67

# 3. Trigger matchdata update
curl -X PUT http://localhost:8000/api/matchdata/67/ \
  -H "Content-Type: application/json" \
  -d '{"score_team_b": 42}'

# 4. Check backend logs for:
# - "matchdata_change notification received"
# - "Processing match-update for match 67"
# - "Sent full match data for match 67"

# 5. Check frontend WebSocket messages (DevTools → Network → WS):
# - Should see full match-update message (~5KB)
# - All fields included: match_data, teams_data, scoreboard_data, players, events

# 6. Check frontend console:
# - wsService.matchDataPartial() should be set
# - UI should update score to 42
```

---

## Related Files

### Backend

- **WebSocket Manager:** `src/utils/websocket/websocket_manager.py`
  - `MatchDataWebSocketManager` - Database listeners
  - `ConnectionManager` - Client queues and subscriptions
- **WebSocket Handler:** `src/websocket/match_handler.py`
  - `MatchWebSocketHandler` - Message processing
  - `process_match_data()` - Fetch and send match data
- **Fetch Helpers:** `src/helpers/fetch_helpers.py`
  - `fetch_with_scoreboard_data()` - Comprehensive data fetch
  - `fetch_gameclock()` - Game clock data
  - `fetch_playclock()` - Play clock data
- **Database Triggers:** `alembic/versions/2026_01_27_1000-stab147_matchdata.py`
  - `notify_matchdata_change()` - PostgreSQL trigger function

### Frontend

- **WebSocket Service:** `../frontend-angular-signals/src/app/core/services/websocket.service.ts`
  - `WebSocketService` - Connection and message handling
  - `handleMessage()` - Message routing
  - Partial update signals
- **Scoreboard View:** `../frontend-angular-signals/src/app/features/scoreboard/pages/view/scoreboard-view.component.ts`
  - Effects for merging partial updates
  - Computed properties for UI

---

## Summary

- **Initial load:** Full data (~5-10KB) on connection
- **Match updates:** Partial data (~200-400B) on matchdata/scoreboard changes (UPDATE/INSERT); full data (~3-8KB) on DELETE/legacy triggers
- **Clock updates:** Partial clock data (~200-400B) on clock changes
- **Event updates:** Full events list with player relationships (~1-5KB) on event changes (fetched fresh)
- **Stats updates:** Full statistics (~1-2KB) on event changes
- **Players updates:** Full players list (~1-5KB) on player_match changes
- **Cache strategy:** Invalidate before fetch for match-update, players-update, and event-update; forward for clocks
- **Queue system:** Per-client async queues decouple message generation from sending
