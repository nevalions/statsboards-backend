# Clock Handling System Documentation

## Overview

The clock handling system manages real-time **playclocks** and **gameclocks** for live sports matches. It provides accurate time tracking with synchronized updates across all connected clients via WebSockets.

### Key Characteristics

- **Dual Clock Types:** PlayClock (typically 24-30 seconds) and GameClock (typically 720+ seconds)
- **State Machine Based:** Both clocks use identical state machine logic
- **Orchestrated Updates:** Single orchestrator coordinates periodic checks for all clocks
- **Database-Driven Notifications:** PostgreSQL triggers push notifications only on actual state changes
- **Queue-Based Message Passing:** AsyncIO queues coordinate updates between components
- **Client-Side Timing:** Clients receive start timestamp and calculate current value locally

---

## Architecture Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Client Applications                           │
│                    (Admin, Scoreboard, Views)                       │
└────────────────────────────────┬────────────────────────────────────────────┘
                             │ HTTP & WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        API Layer (Views)                               │
│  - start_playclock_endpoint / start_gameclock_endpoint                 │
│  - stop/pause/reset endpoints                                         │
└────────┬───────────────────────────────────────┬──────────────────────┘
         │                               │
         │ Service calls                   │ DB updates
         ▼                               ▼
┌──────────────────────┐      ┌─────────────────────────────────────────────┐
│   Service Layer    │      │        PostgreSQL Database              │
│  - update()        │      │  - playclock table                    │
│  - get_by_id()     │      │  - gameclock table                    │
│  - trigger_update_*│      │  - Triggers:                         │
│  - cache_service   │      │    notify_playclock_change             │
└───┬──────────────┘      │    notify_gameclock_change             │
    │                     └───┬───┴──────────────────────────────────────┘
    │ Clock callbacks          │ pg_notify()
    ▼                          │
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Clock Orchestrator                                 │
│  - Main loop (100ms)                                             │
│  - Tracks all running clocks                                         │
│  - Calls service callbacks on second boundaries                         │
└───┬───────────────┬──────────────────────────────────────────────────┘
    │               │
    ▼               ▼
┌───────────────────┐  ┌─────────────────────────────────────────────┐
│ Clock Manager    │  │      WebSocket Manager                  │
│  - Queues       │  │  - Connection management                │
│  - State Machines│  │  - Message queuing                  │
└───────────────────┘  │  - Channel listeners                 │
                      └──────────────────────────────────────────────┘
                              ▲
                              │ pg_notify subscriptions
                              │
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WebSocket Handler                                   │
│  - process_playclock_data()                                         │
│  - process_gameclock_data()                                         │
│  - Sends updates to all connected clients                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Clock State Machine

### Location
- PlayClock: `src/playclocks/clock_state_machine.py`
- GameClock: `src/gameclocks/clock_state_machine.py`

### Implementation

Both clocks use identical state machine logic:

```python
class ClockStateMachine:
    def __init__(self, clock_id: int, initial_value: int) -> None:
        self.clock_id = clock_id
        self.value = initial_value          # Current clock value (seconds)
        self.status = "stopped"            # "stopped", "running", "paused"
        self.started_at_ms: int | None = None  # Start timestamp (milliseconds)
```

### State Transitions

```
    start()                    stop()
stopped ───────────────────▶ running ───────────────────▶ stopped
                             │
                             └── pause() ───────────▶ paused
                                    │
                                    └── start()
                                         │
                                         ▼
                                      running
```

### State Methods

#### `start()`
```python
def start(self) -> None:
    self.started_at_ms = int(time.time() * 1000)
    self.status = "running"
```
- Records start time
- Sets status to "running"

#### `stop()`
```python
def stop(self) -> None:
    self.value = self.get_current_value()
    self.status = "stopped"
    self.started_at_ms = None
```
- Calculates final value based on elapsed time
- Resets to stopped state
- Clears start timestamp

#### `pause()`
```python
def pause(self) -> None:
    self.value = self.get_current_value()
    self.status = "paused"
    self.started_at_ms = None
```
- Calculates current value
- Sets status to "paused"
- Clears start timestamp (can resume later)

### Current Value Calculation

```python
def get_current_value(self) -> int:
    if self.status != "running" or self.started_at_ms is None:
        return self.value
    
    elapsed_ms = int(time.time() * 1000) - self.started_at_ms
    elapsed_sec = elapsed_ms // 1000
    return max(0, self.value - elapsed_sec)
```

**Logic:**
1. If not running or no start time, return stored value
2. Calculate elapsed time since `started_at_ms`
3. Subtract elapsed seconds from initial value
4. Use `max(0, ...)` to prevent negative values (floor at 0)

**Important:** The state machine calculates values on-the-fly - it doesn't update the database every second. The database only stores the initial value and start timestamp.

---

## 2. Clock Manager

### Location
- PlayClock: `src/playclocks/clock_manager.py`
- GameClock: Inline in `src/gameclocks/db_services.py` (lines 15-44)

### Implementation

```python
class ClockManager:
    def __init__(self) -> None:
        self.active_playclock_matches: dict[int, asyncio.Queue] = {}
        self.clock_state_machines: dict[int, ClockStateMachine] = {}
```

### Key Methods

#### `start_clock(match_id, initial_value)`
Creates queue and state machine for a clock:
```python
async def start_clock(self, match_id: int, initial_value: int = 0) -> None:
    if match_id not in self.active_playclock_matches:
        self.active_playclock_matches[match_id] = asyncio.Queue()
    if match_id not in self.clock_state_machines:
        self.clock_state_machines[match_id] = ClockStateMachine(
            match_id, initial_value
        )
```

#### `end_clock(match_id)`
Cleans up clock resources:
```python
async def end_clock(self, match_id: int) -> None:
    if match_id in self.active_playclock_matches:
        del self.active_playclock_matches[match_id]
    if match_id in self.clock_state_machines:
        del self.clock_state_machines[match_id]
```

#### `update_queue_clock(match_id, message)`
Pushes updates to clock's queue:
```python
async def update_queue_clock(self, match_id: int, message: PlayClockDB) -> None:
    if match_id in self.active_playclock_matches:
        queue = self.active_playclock_matches[match_id]
        await queue.put(message)
```

---

## 3. Clock Orchestrator

### Location
`src/clocks/clock_orchestrator.py`

### Purpose
Coordinates periodic updates for all running clocks using a single main loop.

### Implementation

```python
class ClockOrchestrator:
    def __init__(self) -> None:
        self.running_playclocks: dict[int, object] = {}
        self.running_gameclocks: dict[int, object] = {}
        self._task: asyncio.Task | None = None
        self._is_running = False
        self._playclock_update_callback: callable | None = None
        self._gameclock_update_callback: callable | None = None
```

### Main Loop

Runs every 100 milliseconds:

```python
async def _run_loop(self) -> None:
    while self._is_running:
        now = time.monotonic()
        
        # Check all running playclocks
        for clock_id, state_machine in list(self.running_playclocks.items()):
            if self._should_update(now, state_machine):
                await self._update_playclock(clock_id, state_machine)
        
        # Check all running gameclocks
        for clock_id, state_machine in list(self.running_gameclocks.items()):
            if self._should_update(now, state_machine):
                await self._update_gameclock(clock_id, state_machine)
        
        await asyncio.sleep(0.1)  # Sleep 100ms
```

### Update Decision Logic

```python
def _should_update(self, now: float, state_machine: object) -> bool:
    if not hasattr(state_machine, "started_at_ms") or state_machine.started_at_ms is None:
        return False
    
    elapsed = now - (state_machine.started_at_ms / 1000.0)
    current_second = int(elapsed)
    next_update = current_second + 1
    time_until_next = next_update - elapsed
    return time_until_next <= 0.1
```

**Logic:**
1. Calculate elapsed time since start (in seconds)
2. Determine when next second boundary occurs
3. Return `True` if within 0.1 seconds of next second boundary
4. This ensures updates happen exactly once per second

### Service Callbacks

The orchestrator doesn't update databases directly. Instead, it calls service callbacks:

```python
async def _update_playclock(self, clock_id: int, state_machine: object) -> None:
    current_value = state_machine.get_current_value()
    
    if current_value == 0:
        # Clock expired - stop it
        if self._playclock_stop_callback:
            await self._playclock_stop_callback(clock_id)
        self.unregister_playclock(clock_id)
    else:
        # Clock still running - trigger update notification
        if self._playclock_update_callback:
            await self._playclock_update_callback(clock_id)
```

**Service Layer Implementation** (`src/playclocks/db_services.py`):

```python
async def trigger_update_playclock(self, playclock_id: int) -> None:
    """Called by orchestrator every second - fetches from DB and pushes to queue"""
    playclock: PlayClockDB | None = await self.get_by_id(playclock_id)
    
    active_clock_matches = self.clock_manager.active_playclock_matches
    
    if playclock_id in active_clock_matches:
        matchdata_clock_queue = active_clock_matches[playclock_id]
        await matchdata_clock_queue.put(playclock)
```

**Important:** The orchestrator callback fetches fresh data from DB and pushes to queue. It does **not** directly update the database every second. The database is only updated on state changes (start, stop, pause, reset).

---

## 4. Database Triggers

### Location
`alembic/versions/2026_01_24_1600-stab133_clock_status_and_value_notify.py`

### PlayClock Trigger

```sql
CREATE OR REPLACE FUNCTION notify_playclock_change() RETURNS trigger AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        PERFORM pg_notify('playclock_change', json_build_object(
            'table', TG_TABLE_NAME,
            'operation', TG_OP,
            'match_id', OLD.match_id,
            'data', json_build_object(
                'id', OLD.id,
                'match_id', OLD.match_id,
                'version', OLD.version,
                'playclock', OLD.playclock,
                'playclock_status', OLD.playclock_status
            )
        )::text);
    ELSE
        -- Only notify on status OR value changes
        IF OLD.playclock_status IS DISTINCT FROM NEW.playclock_status
           OR OLD.playclock IS DISTINCT FROM NEW.playclock THEN
            PERFORM pg_notify('playclock_change', json_build_object(
                'table', TG_TABLE_NAME,
                'operation', TG_OP,
                'match_id', NEW.match_id,
                'data', json_build_object(
                    'id', NEW.id,
                    'match_id', NEW.match_id,
                    'version', NEW.version,
                    'playclock', NEW.playclock,
                    'playclock_status', NEW.playclock_status
                )
            )::text);
        END IF;
    END IF;
    RETURN new;
END;
$$ LANGUAGE plpgsql;
```

### GameClock Trigger

Similar structure, but includes additional fields (`gameclock_time_remaining`, `gameclock_max`).

### When Triggers Fire

| Event | Fires? | Condition |
|-------|--------|-----------|
| INSERT | Yes | Always |
| UPDATE | **Yes only if** | `status` OR `value` changes (`IS DISTINCT FROM`) |
| UPDATE | **No** | If only `version` or other non-critical fields change |
| DELETE | Yes | Always |

**Key Point:** Triggers use `IS DISTINCT FROM` to compare old/new values. This means:
- `NULL` is properly compared with actual values
- Only meaningful changes trigger notifications
- Version bumps alone don't trigger (reduces unnecessary WebSocket traffic)

---

## 5. WebSocket Flow

### Listener Setup
`src/utils/websocket/websocket_manager.py`

```python
async def setup_listeners(self):
    listeners = {
        "playclock_change": self.playclock_listener,
        "gameclock_change": self.gameclock_listener,
        # ... other listeners
    }
    
    for channel, listener in listeners.items():
        await self.connection.add_listener(channel, listener)
```

### Notification Processing

```python
async def playclock_listener(self, connection, pid, channel, payload):
    # Invalidate cache first
    invalidate_func = self._cache_service.invalidate_playclock if self._cache_service else None
    
    # Base listener processes notification
    await self._base_listener(
        connection,
        pid,
        channel,
        payload,
        "playclock-update",  # Message type sent to clients
        self.playclock_queues,  # Queue dictionary
        invalidate_func,
    )
```

### Base Listener Logic

```python
async def _base_listener(
    self, connection, pid, channel, payload, update_type, queue_dict, invalidate_func=None
):
    # 1. Parse payload
    data = json.loads(payload.strip())
    match_id = data["match_id"]
    data["type"] = update_type  # e.g., "playclock-update"
    
    # 2. Invalidate cache
    if invalidate_func and self._cache_service:
        invalidate_func(match_id)  # invalidate_playclock(match_id)
    
    # 3. Get all subscribed clients for this match
    clients = await connection_manager.get_match_subscriptions(match_id)
    
    # 4. Queue message for each subscribed client
    for client_id in clients:
        if client_id in queue_dict:
            await queue_dict[client_id].put(data)
    
    # 5. Also send to all clients in match channels
    await connection_manager.send_to_all(data, match_id=match_id)
```

### Client Message Processing
`src/websocket/match_handler.py`

```python
async def process_playclock_data(
    self, websocket: WebSocket, match_id: int, data: dict | None = None
):
    try:
        if websocket.application_state != WebSocketState.CONNECTED:
            return
        
        # Fetch current playclock data from DB (uses cache if available)
        playclock_data = await fetch_playclock(match_id, cache_service=self.cache_service)
        playclock_data["type"] = "playclock-update"
        
        # Send to client
        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.send_json(playclock_data)
    except Exception as e:
        self.logger.error(f"Error processing playclock data: {e}", exc_info=True)
```

**Important:** When a notification is received, the handler **doesn't use notification data directly**. It fetches fresh data from the database (via cache service) to ensure clients receive the most up-to-date state.

### Cache Management
`src/matches/match_data_cache_service.py`

```python
def invalidate_playclock(self, match_id: int) -> None:
    cache_key = f"playclock-update:{match_id}"
    if cache_key in self._cache:
        del self._cache[cache_key]

async def get_or_fetch_playclock(self, match_id: int) -> dict | None:
    cache_key = f"playclock-update:{match_id}"
    if cache_key in self._cache:
        return self._cache[cache_key]
    
    result = await fetch_playclock(match_id, database=self.db)
    if result and "playclock" in result:
        self._cache[cache_key] = result
        return result
    return None
```

---

## 6. Clock Operations

### Starting a Clock

#### PlayClock
**Endpoint:** `PUT /api/playclock/id/{item_id}/running/{sec}/`

```python
async def start_playclock_endpoint(
    background_tasks: BackgroundTasks,
    item_id: int,
    sec: int,
):
    # 1. Enable queues and create state machine if needed
    await self.service.enable_match_data_clock_queues(item_id, sec)
    
    # 2. Check if already running
    item = await self.service.get_by_id(item_id)
    if item.playclock_status != "running":
        started_at_ms = int(time.time() * 1000)
        
        # 3. Update database (atomic update with all fields)
        await self.service.update(
            item_id,
            PlayClockSchemaUpdate(
                playclock=sec,
                playclock_status="running",
                started_at_ms=started_at_ms,
            ),
        )
        
        # 4. Update state machine
        state_machine = self.service.clock_manager.get_clock_state_machine(item_id)
        if not state_machine:
            await self.service.clock_manager.start_clock(item_id, sec)
        if state_machine:
            state_machine.started_at_ms = started_at_ms
            state_machine.status = "running"
    
    updated = await self.service.get_by_id(item_id)
    return self.create_response_with_server_time(updated, f"Playclock ID:{item_id} running")
```

**Data Flow:**
```
Client Request
    │
    ▼
Enable Queues (create state machine)
    │
    ▼
DB Update (atomic)
    │
    ▼
Trigger Fires (notify_playclock_change)
    │
    ▼
pg_notify('playclock_change', {...})
    │
    ▼
WebSocket Listener
    │
    ├─▶ Cache Invalidation
    └─▶ Queue for clients
        │
        ▼
WebSocket Handler
    │
    └─▶ Fetch fresh data (cache miss)
        │
        ▼
    └─▶ Send to clients
```

#### GameClock
**Endpoint:** `PUT /api/gameclock/id/{gameclock_id}/running/`

Similar flow, but uses `gameclock.gameclock` value from database instead of URL parameter.

### Pausing a Clock

**Note:** Only GameClock has a dedicated pause endpoint. PlayClock uses reset endpoints.

#### GameClock Pause
**Endpoint:** `PUT /api/gameclock/id/{item_id}/paused/`

```python
async def pause_gameclock_endpoint(item_id: int):
    # 1. Get current value from state machine or DB
    state_machine = self.service.clock_manager.get_clock_state_machine(item_id)
    current_value = None
    
    if state_machine:
        current_value = state_machine.get_current_value()
    else:
        gameclock_db = await self.service.get_by_id(item_id)
        if gameclock_db:
            current_value = gameclock_db.gameclock
    
    # 2. Stop orchestrator tracking
    await self.service.stop_gameclock(item_id)
    
    # 3. Update database
    updated = await self.service.update(
        item_id,
        GameClockSchemaUpdate(
            gameclock_status="paused",
            gameclock=current_value,
            gameclock_time_remaining=current_value,
            started_at_ms=None,
        ),
    )
```

### Stopping a Clock

#### PlayClock Stop
**Endpoint:** `PUT /api/playclock/id/{item_id}/{item_status}/{sec}/`

Can set status to "stopped" with a specific value.

#### GameClock Stop
GameClocks are stopped by:
1. Pausing (sets status to "paused")
2. Running down to 0 (orchestrator auto-stops)
3. Resetting to new value

### Resetting a Clock

#### PlayClock Reset
**Endpoints:**
- `PUT /api/playclock/id/{item_id}/{item_status}/{sec}/` - Reset to specific value
- `PUT /api/playclock/id/{item_id}/stopped/` - Reset to stopped with `playclock=None`

```python
async def reset_playclock_stopped_endpoint(item_id: int):
    updated = await self.service.update_with_none(
        item_id,
        PlayClockSchemaUpdate(
            playclock=None,
            playclock_status="stopped",
        ),
    )
```

#### GameClock Reset
**Endpoint:** `PUT /api/gameclock/id/{item_id}/{item_status}/{sec}/`

```python
async def reset_gameclock_endpoint(
    item_id: int,
    item_status: str = "stopped",
    sec: int = 720,
):
    updated = await self.service.update(
        item_id,
        GameClockSchemaUpdate(
            gameclock=sec,
            gameclock_status=item_status,
        ),
    )
    
    if updated:
        self.service.cache_service.invalidate_gameclock(item_id)
```

---

## 7. Complete Data Flow Examples

### Scenario: Starting a PlayClock

```
1. Client Request
   PUT /api/playclock/id/123/running/25/
   
2. Service Layer (enable_match_data_clock_queues)
   ├─▶ clock_manager.start_clock(123, 25)
   │   ├─▶ Create asyncio.Queue for match 123
   │   └─▶ Create ClockStateMachine(123, 25)
   │
   ├─▶ state_machine.start() [sets started_at_ms=..., status="running"]
   └─▶ clock_orchestrator.register_playclock(123, state_machine)

3. Service Layer (update - atomic)
   └─▶ UPDATE playclock SET
       playclock=25,
       playclock_status='running',
       started_at_ms=1737724800000
       WHERE id=123

4. Database Trigger
   └─▶ notify_playclock_change() fires
       └─▶ pg_notify('playclock_change', {
           "table": "playclock",
           "operation": "UPDATE",
           "match_id": 123,
           "data": {
               "id": 456,
               "match_id": 123,
               "version": 10,
               "playclock": 25,
               "playclock_status": "running"
           }
       })

5. WebSocket Listener (playclock_listener)
   ├─▶ Invalidate cache: "playclock-update:123"
   └─▶ Queue message for all subscribed clients
       └─▶ {type: "playclock-update", match_id: 123, data: {...}}

6. WebSocket Handler (process_playclock_data)
   ├─▶ fetch_playclock(123) [cache miss, fetch from DB]
   │   └─▶ Returns {playclock: 25, playclock_status: "running", ...}
   └─▶ Send to client via WebSocket

7. Client Receives
   {
     "type": "playclock-update",
     "match_id": 123,
     "playclock": {
       "id": 456,
       "match_id": 123,
       "version": 10,
       "playclock": 25,
       "playclock_status": "running",
       "started_at_ms": 1737724800000
     },
     "server_time_ms": 1737724800050
   }
```

### Scenario: Running Clock (Every Second)

```
1. Orchestrator Loop (every 100ms)
   └─▶ _run_loop()
       └─▶ Check all running playclocks
           └─▶ should_update(123, state_machine)?
               └─▶ elapsed=2.8s, next_update in 0.2s? YES

2. Orchestrator (_update_playclock)
   └─▶ state_machine.get_current_value() = 22
       └─▶ current_value > 0? YES
           └─▶ _playclock_update_callback(123) [service callback]

3. Service Callback (trigger_update_playclock)
   └─▶ get_by_id(123) [fetches from DB - NO DB UPDATE!]
       └─▶ Returns PlayClockDB with:
           playclock=25,
           playclock_status="running",
           started_at_ms=1737724800000
       └─▶ active_playclock_matches[123].put(playclock)
           └─▶ Push to manager's queue (not used by WebSocket)

4. Database
   └─▶ NO UPDATE - triggers don't fire
   └─▶ Clients continue using stored started_at_ms
       └─▶ Client calculates: current = 25 - floor((now - 1737724800000) / 1000)
           └─▶ After 3 seconds: current = 22
```

**Key Points:**
- Orchestrator tracks clocks in memory and checks every 100ms
- Database is **not** updated every second (only on state changes)
- Clients receive `started_at_ms` timestamp on start
- Clients calculate current value locally using that timestamp
- No WebSocket traffic every second (reduces load)

### Scenario: Clock Reaches Zero

```
1. Orchestrator Loop
   └─▶ Check playclock 123
       └─▶ state_machine.get_current_value() = 0

2. Orchestrator (_update_playclock)
   └─▶ current_value == 0? YES
       └─▶ _playclock_stop_callback(123)

3. Service Callback (stop_playclock_internal)
   ├─▶ UPDATE playclock SET
   │       playclock=0,
   │       playclock_status='stopped',
   │       started_at_ms=NULL
   │       WHERE id=123
   │
   ├─▶ Trigger fires
   │   └─▶ pg_notify('playclock_change', {...})
   └─▶ clock_orchestrator.unregister_playclock(123)

4. Cleanup
   ├─▶ Orchestrator removes from running_playclocks dict
   └─▶ clock_manager.end_clock(123)
       ├─▶ Delete queue
       └─▶ Delete state machine

5. WebSocket Notification
   └─▶ Clients receive {playclock_status: "stopped", playclock: 0}
```

---

## 8. Differences Between PlayClock and GameClock

| Aspect | PlayClock | GameClock |
|--------|-----------|-----------|
| **Typical Values** | 24-30 seconds | 720+ seconds (12+ minutes) |
| **Database Fields** | `playclock`, `playclock_status`, `started_at_ms` | `gameclock`, `gameclock_status`, `gameclock_time_remaining`, `gameclock_max`, `started_at_ms` |
| **Pause Endpoint** | No (use reset) | Yes (`/paused/`) |
| **Set to None** | Can set `playclock=None` on stop | No "set to None" functionality |
| **Queue Dict Name** | `active_playclock_matches` | `active_gameclock_matches` |
| **State Machine** | Separate file | Inline in db_services.py |
| **Manager** | Separate file | Inline in db_services.py |
| **Reset URL** | `/id/{item_id}/{item_status}/{sec}/` | `/id/{item_id}/{item_status}/{sec}/` |

---

## 9. Key Architectural Patterns

### 1. State Machine Pattern
Both clocks use identical `ClockStateMachine` with:
- 3 states: stopped, running, paused
- Timestamp-based value calculation
- On-the-fly computation (no DB writes per second)

### 2. Orchestrator Pattern
Single `ClockOrchestrator` instance:
- Runs one loop at 100ms intervals
- Checks all clocks for second-boundary updates
- Uses callbacks to avoid tight coupling

### 3. Queue-Based Updates
Each clock has an `asyncio.Queue`:
- Message passing between components
- Manager tracks queues per clock
- WebSocket uses separate connection manager queues

### 4. Database-Driven Notifications
PostgreSQL `pg_notify` triggers:
- Fire only on actual DB changes
- Send structured JSON payloads
- Use `IS DISTINCT FROM` to reduce noise

### 5. Cache Invalidation
Cache keys match message types:
- PlayClock: `playclock-update:{match_id}`
- GameClock: `gameclock-update:{match_id}`
- Invalidated on trigger receipt
- Refreshed on fetch

### 6. Separation of Concerns
| Component | Responsibility |
|-----------|---------------|
| **State Machine** | In-memory timing logic |
| **Orchestrator** | Coordinates periodic checks |
| **Database** | Source of truth for state changes |
| **Triggers** | Push notifications for DB changes |
| **WebSocket** | Real-time delivery to clients |
| **Cache** | Reduces DB load for frequent reads |

---

## 10. Performance Considerations

### Database Load
- **Minimal writes:** Database only updated on state changes (start/stop/pause/reset), not every second
- **Optimized reads:** Cache service reduces DB fetches
- **Efficient triggers:** Only fire on meaningful changes (status or value)

### WebSocket Traffic
- **State changes only:** One notification per start/stop/pause/reset
- **No per-second spam:** Clients use timestamp to calculate locally
- **Targeted delivery:** Only subscribed clients receive messages

### Memory Usage
- **State machines:** Small in-memory objects per active clock
- **Queues:** One `asyncio.Queue` per clock
- **Orchestrator:** Single dictionary tracking all active clocks

### Scalability
- **Multiple matches:** Independent state machines per clock
- **Concurrent updates:** AsyncIO handles multiple clocks in parallel
- **No locks:** Queue-based message passing avoids blocking

---

## 11. Client-Side Calculation

Clients receive the start timestamp and calculate current value locally:

```javascript
// Example: Client-side playclock display
function calculateCurrentPlayclock(startTimeMs, initialValue) {
    const now = Date.now();
    const elapsedMs = now - startTimeMs;
    const elapsedSec = Math.floor(elapsedMs / 1000);
    const current = Math.max(0, initialValue - elapsedSec);
    return current;
}

// When playclock starts:
playclock.startTimeMs = data.playclock.started_at_ms;
playclock.initialValue = data.playclock.playclock;

// Update display (e.g., every 100ms):
playclock.currentValue = calculateCurrentPlayclock(
    playclock.startTimeMs,
    playclock.initialValue
);
```

**Benefits:**
- Smooth UI updates independent of network latency
- Consistent display across all clients
- No need for frequent WebSocket messages

---

## 12. Common Issues and Solutions

### Issue: Clock Shows Wrong Value in Different Tabs

**Symptom:** Clock shows correct value in admin tab but stale value in other tabs/view.

**Root Cause:** Two separate DB updates causing inconsistent WebSocket notifications with race condition.

**Solution:** Combined atomic update with all fields (status, value, started_at_ms).

### Issue: Clock Not Updating Every Second

**Symptom:** Clock value doesn't decrement during match.

**Possible Causes:**
1. Orchestrator not running (check `_is_running` flag)
2. Clock not registered with orchestrator
3. State machine status not set to "running"
4. `started_at_ms` is `None`

**Solution:** Verify orchestrator startup and clock registration flow.

### Issue: WebSocket Notifications Not Received

**Symptom:** Changes in one tab don't reflect in other tabs.

**Possible Causes:**
1. Triggers not notifying on value changes
2. Listener not subscribed to correct channel
3. Cache not invalidated after update

**Solution:** Check trigger conditions (`IS DISTINCT FROM`) and listener setup.

### Issue: Negative Clock Values

**Symptom:** Clock shows negative numbers after reaching zero.

**Root Cause:** State machine doesn't enforce floor at 0.

**Solution:** State machine uses `max(0, ...)` to prevent negative values.

---

## 13. Troubleshooting

### Enable Debug Logging

```python
# Clock state machine
logger.setLevel(logging.DEBUG)

# Orchestrator
orchestrator_logger.setLevel(logging.DEBUG)

# WebSocket manager
websocket_logger.setLevel(logging.DEBUG)
```

### Monitor Database Notifications

```sql
-- Monitor playclock notifications in PostgreSQL
LISTEN playclock_change;

-- Monitor gameclock notifications
LISTEN gameclock_change;
```

### Check Active Clocks

```python
# PlayClock
playclock_manager = PlayClockServiceDB(db)
print(f"Active playclocks: {playclock_manager.clock_manager.active_playclock_matches.keys()}")

# GameClock
gameclock_manager = GameClockServiceDB(db)
print(f"Active gameclocks: {gameclock_manager.clock_manager.active_gameclock_matches.keys()}")

# Orchestrator
from src.clocks.clock_orchestrator import clock_orchestrator
print(f"Running playclocks: {clock_orchestrator.running_playclocks.keys()}")
print(f"Running gameclocks: {clock_orchestrator.running_gameclocks.keys()}")
```

### Verify Cache State

```python
cache_service = MatchDataCacheService(db)
cache_key = f"playclock-update:{match_id}"
if cache_key in cache_service._cache:
    print(f"Cached data: {cache_service._cache[cache_key]}")
else:
    print("No cached data")
```

---

## Summary

The clock handling system provides:

1. **Real-time Synchronization:** All clients see identical clock values
2. **Efficient Updates:** Minimal database writes and WebSocket traffic
3. **Client-Side Timing:** Smooth UI updates independent of network
4. **Scalable Architecture:** Handles multiple matches concurrently
5. **Robust State Management:** Clear state transitions and error handling
6. **Database-Driven Notifications:** PostgreSQL triggers ensure consistency
7. **Caching Layer:** Reduces database load for frequent reads

The system balances accuracy, performance, and scalability by using in-memory state machines for timing calculations, database for state persistence, and WebSockets for real-time delivery.
