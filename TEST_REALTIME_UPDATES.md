# Test Plan: Real-time Match Data Updates Not Working

## Issue Summary
Match data changes are not being reflected in the frontend in real-time despite backend confirmed changes.

## Context
- Backend and frontend STAB/STAF Linear issues have been implemented
- WebSocket architecture is in place with NOTIFY triggers
- Frontend has WebSocket service and signal-based state management
- Real-time updates are not occurring

## Testing Instructions

### Prerequisites
1. Backend server running with debug logging enabled
2. Frontend running (development mode)
3. Database with test match data
4. Browser DevTools open (F12)

### Step 1: Verify WebSocket Connection

#### Frontend (Browser Console)
```
1. Navigate to a match page (e.g., /matches/123)
2. Open DevTools → Console tab
3. Look for these log messages:

✓ [WebSocket] Connecting...
✓ [WebSocket] Connected successfully
✓ [WebSocket] Initial load data received via WebSocket

✗ [WebSocket] Connection failed
✗ [WebSocket] Max retry attempts reached
✗ [WebSocket] Connection error: ...
```

**Report:**
- [ ] WebSocket connects successfully
- [ ] Initial load data received
- [ ] Any errors observed (paste here): ______________________________

#### Backend (Terminal)
```
Look for these log messages:

✓ Connecting to WebSocket at WebSocket(..., state=WebSocketState.CONNECTED) with client_id: ... and match_id: ...
✓ Match subscription added {...}
✓ WebSocket Connection sending initial-load message
✓ WebSocket Connection combined initial_data: {...}

✗ Client {client_id} disconnected (if frequent, connection dropping)
✗ No queue found for client_id {client_id}. Data not enqueued.
```

**Report:**
- [ ] Client connected to WebSocket
- [ ] Initial data sent
- [ ] Match subscribed correctly
- [ ] Any errors observed (paste here): ______________________________

---

### Step 2: Test Database NOTIFY Triggers

#### Terminal 1: Listen for Notifications
```bash
psql $DATABASE_URL
LISTEN matchdata_change;
LISTEN scoreboard_change;
LISTEN football_event_change;
LISTEN gameclock_change;
LISTEN playclock_change;
```

#### Terminal 2: Trigger a Database Change
```bash
# Replace 123 with a real match_id from your database
psql $DATABASE_URL -c "UPDATE matchdata SET home_score = home_score + 1 WHERE match_id = 123;"

# Then immediately check if notification was received in Terminal 1
```

**Report:**
- [ ] NOTIFY received in Terminal 1
- [ ] Payload contains correct match_id
- [ ] Notification latency: _______ seconds

---

### Step 3: Test Full Update Chain

#### Make a Match Data Change
```
1. In browser console or via API, update match data:
   - Example: POST to /api/matches/123/ with updated scoreboard

2. Watch Backend Logs for:
   ✓ "matchdata_change" notification received
   ✓ Added match-update to queue for client {client_id}
   ✓ Processing match data type: match-update for match 123
   ✓ Match data fetched: {...}

3. Watch Browser Console for:
   ✓ [WebSocket] Match data update
   ✓ Match data update received

4. Check UI:
   [ ] Score updated on page
   [ ] Changes visible immediately (within 1-2 seconds)
```

**Report:**
- [ ] Backend received notification
- [ ] Backend sent message to queue
- [ ] Frontend received message
- [ ] UI updated
- [ ] Time from DB change to UI update: _______ seconds

---

### Step 4: Test Specific Update Types

#### A. Scoreboard Updates
```bash
# Update scoreboard data
psql $DATABASE_URL -c "UPDATE scoreboard SET is_flag = true WHERE match_id = 123;"

Expected:
- Backend: "scoreboard_change" notification
- Frontend: scoreboardPartial signal updated
- UI: Flag indicator appears
```

**Report:**
- [ ] Scoreboard updates work
- [ ] Errors: ______________________________

#### B. Event Updates
```bash
# Create a new football event
psql $DATABASE_URL -c "INSERT INTO football_event (match_id, event_type, quarter, time_remaining) VALUES (123, 'touchdown', 1, '12:00');"

Expected:
- Backend: "football_event_change" notification (may be throttled 2s)
- Frontend: events signal updated
- UI: New event appears in event list
```

**Report:**
- [ ] Event updates work
- [ ] Throttle delay observed: _______ seconds
- [ ] Errors: ______________________________

#### C. Clock Updates (Critical)
```bash
# Update gameclock
psql $DATABASE_URL -c "UPDATE gameclock SET status = 'running' WHERE match_id = 123;"

Expected:
- Backend: "gameclock_change" notification
- Frontend: gameClock signal updated
- UI: Clock starts ticking

Note: Clocks must be registered with orchestrator for this to work
```

**Report:**
- [ ] Gameclock updates work
- [ ] Playclock updates work
- [ ] Clocks registered with orchestrator
- [ ] Errors: ______________________________

---

### Step 5: Clock Orchestrator Registration

If clock updates are NOT working, check:

```bash
# Look for these backend logs:
✓ Clock registered with orchestrator: {gameclock_id}
✗ Clock not registered with orchestrator: {gameclock_id}, update queued but not processed
```

**Report:**
- [ ] Clocks registered
- [ ] Active gameclock matches include your match_id
- [ ] Registration method called from frontend
- [ ] Errors: ______________________________

---

### Step 6: Check WebSocket Manager Listeners

In backend startup logs, look for:

```
✓ Successfully added listener for channel: matchdata_change
✓ Successfully added listener for channel: scoreboard_change
✓ Successfully added listener for channel: playclock_change
✓ Successfully added listener for channel: gameclock_change
✓ Successfully added listener for channel: football_event_change

✗ Error setting up listener for {channel}: ...
```

**Report:**
- [ ] All listeners successfully added
- [ ] Any listener errors: ______________________________

---

## Diagnostic Results Template

### Connection Status
- WebSocket Connected: [ ] Yes [ ] No
- Initial Data Loaded: [ ] Yes [ ] No
- Client Subscribed to Match: [ ] Yes [ ] No

### Update Test Results
| Update Type | DB Notify Received | Backend Queued | Frontend Received | UI Updated | Notes |
|------------|-------------------|----------------|-------------------|------------|-------|
| Match Data | [ ] [ ] | [ ] [ ] | [ ] [ ] | [ ] [ ] | |
| Scoreboard | [ ] [ ] | [ ] [ ] | [ ] [ ] | [ ] [ ] | |
| Events | [ ] [ ] | [ ] [ ] | [ ] [ ] | [ ] [ ] | |
| Gameclock | [ ] [ ] | [ ] [ ] | [ ] [ ] | [ ] [ ] | |
| Playclock | [ ] [ ] | [ ] [ ] | [ ] [ ] | [ ] [ ] | |

### Identified Issues

Based on testing, the issue appears to be:

- [ ] WebSocket not connecting (frontend issue)
- [ ] WebSocket not subscribing to match (backend issue)
- [ ] Database NOTIFY not firing (trigger issue)
- [ ] WebSocket manager not receiving NOTIFY (listener issue)
- [ ] Client queue not receiving messages (queue issue)
- [ ] Match handler not sending messages (handler issue)
- [ ] Frontend not receiving messages (WebSocket issue)
- [ ] Frontend not processing messages (signal issue)
- [ ] Clocks not registered with orchestrator (clock issue)
- [ ] Other: ______________________________

### Log Samples

**Frontend Console (relevant messages):**
```
(paste here)
```

**Backend Logs (relevant messages):**
```
(paste here)
```

**Database NOTIFY Test:**
```
(paste here)
```

## Next Steps Based on Results

### If WebSocket Not Connecting:
- Check frontend API configuration in `src/app/core/config/api.constants.ts`
- Verify backend WebSocket router is mounted correctly
- Check network tab in browser DevTools for WebSocket errors

### If WebSocket Connects But No Updates:
- Verify database triggers are active: `SELECT tgname FROM pg_trigger WHERE tgname LIKE '%change%';`
- Check if WebSocket manager listeners are registered
- Verify client is in match_subscriptions
- Check if match_stats_throttle table exists and has rows

### If Clocks Not Updating:
- Verify clock orchestrator is running
- Check if clocks are registered when match page loads
- Look for "Clock not registered with orchestrator" warnings

### If Frontend Receives But UI Doesn't Update:
- Check if partial update effects are running
- Verify signals are being set correctly
- Check for computed property issues in components

## Additional Notes

- Test match_id used: _______________
- Browser: _______________
- Backend version: _______________
- Frontend version: _______________
- Database schema version: `alembic current` output: _______________

---

## Related Files

**Backend:**
- `src/websocket/match_handler.py` - WebSocket message processing
- `src/utils/websocket/websocket_manager.py` - NOTIFY listeners and client management
- `src/matches/websocket_router.py` - WebSocket endpoint
- `alembic/versions/2024_03_22_1511-4ac3e0c1b4f1_matchdata_trigger_update_to_send_match_.py` - matchdata NOTIFY trigger
- `alembic/versions/2024_03_22_1525-812a14b18a01_scoreboard_trigger_update_to_send_match_.py` - scoreboard NOTIFY trigger
- `alembic/versions/2026_01_26_2102-stab146_stats_throttling.py` - event NOTIFY trigger with throttling

**Frontend:**
- `src/app/core/services/websocket.service.ts` - WebSocket connection and message handling
- `src/app/features/scoreboard/pages/view/scoreboard-view.component.ts` - View page with partial update effects
- `src/app/features/scoreboard/pages/admin/scoreboard-admin.component.ts` - Admin page with partial update effects
- `src/app/core/config/api.constants.ts` - WebSocket URL configuration

**Database Tables:**
- `matchdata` - Match scores, quarters, etc.
- `scoreboard` - Scoreboard settings
- `football_event` - Game events
- `gameclock` - Game clock state
- `playclock` - Play clock state
- `match_stats_throttle` - Stats throttling (for event NOTIFY)
