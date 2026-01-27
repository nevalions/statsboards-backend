# Frontend Verification Guide for Partial WebSocket Updates

## Backend Changes

### What Changed (STAB-147, STAB-148)

**Before:** Backend sent raw database notifications
```json
{
  "table": "matchdata",
  "operation": "UPDATE",
  "new_id": 67,
  "match_id": 67
}
```

**After (STAB-147, STAB-149):** Backend fetches full match data with all relations

**Database trigger sends:**
```json
{
  "table": "matchdata",
  "operation": "UPDATE",
  "new_id": 67,
  "match_id": 67,
  "data": {
    "id": 67,
    "score_team_a": 7,
    "score_team_b": 3,
    "qtr": "Q2",
    "game_status": "IN_PROGRESS"
    // ... all matchdata fields
  }
}
```

**Backend fetches full data via `fetch_with_scoreboard_data()` and sends:**
```json
{
  "type": "match-update",
  "data": {
    "match_id": 67,
    "id": 67,
    "match": { /* full match object */ },
    "teams_data": { /* team_a, team_b */ },
    "match_data": {
      "id": 67,
      "score_team_a": 7,
      "score_team_b": 3,
      "qtr": "Q2",
      // ... all matchdata fields
    },
    "scoreboard_data": { /* scoreboard settings */ },
    "players": [ /* all players */ ],
    "events": [ /* all events */ ]
  }
}
```

**Note:** Match updates now send **FULL data** (~3-8KB) with all relations, not just changed fields. This ensures consistency across the entire match state.

---

## Frontend Verification Steps

### 1. Open Scoreboard View

```bash
cd ../frontend-angular-signals
npm start
```

Navigate to: `http://localhost:4200/scoreboard/view/67`

### 2. Open Browser DevTools

1. Press `F12` (or right-click → Inspect)
2. Go to **Network** tab
3. Filter by **WS** (WebSocket)
4. Click on WebSocket connection
5. Go to **Messages** tab

### 3. Observe Initial Load

**Expected message:**
```json
{
  "type": "initial-load",
  "data": {
    "match_data": { /* all matchdata fields */ },
    "scoreboard_data": { /* all scoreboard settings */ },
    "gameclock": { /* gameclock data */ },
    "playclock": { /* playclock data */ },
    "events": [ /* all events */ ],
    "teams_data": { /* teams */ },
    "match": { /* match info */ }
  }
}
```

**Message size:** ~5-10KB (full data)

### 4. Trigger Update via API

Open another terminal and update matchdata:

```bash
curl -X PUT http://localhost:8000/api/matchdata/67/ \
  -H "Content-Type: application/json" \
  -d '{
    "score_team_a": 10,
    "qtr": "Q3"
  }'
```

### 5. Observe Match Update in DevTools

**Expected message:**
```json
{
  "type": "match-update",
  "data": {
    "match_id": 67,
    "id": 67,
    "match": { /* full match object */ },
    "teams_data": { /* team_a, team_b */ },
    "match_data": {
      "id": 67,
      "score_team_a": 10,
      "qtr": "Q3"
      // Note: FULL matchdata object, not just changed fields
    },
    "scoreboard_data": { /* scoreboard settings */ },
    "players": [ /* all players */ ],
    "events": [ /* all events */ ]
  }
}
```

**Message size:** ~3-8KB (full data with all relations)

### 6. Verify Frontend Updates

**Expected behavior:**
- Score updates from 7 to 10 immediately
- Quarter updates from "Q2" to "Q3" immediately
- No page reload
- No visible lag

**Signals to check in Console:**
```typescript
// Open Console and type:
wsService.matchDataPartial()  // Should show updated match_data
wsService.scoreboardPartial()  // Should be null (not updated)
wsService.lastMatchDataUpdate()  // Should show timestamp
```

### 7. Test Scoreboard Update

```bash
curl -X PUT http://localhost:8000/api/scoreboards/67/ \
  -H "Content-Type: application/json" \
  -d '{
    "show_team_names": false
  }'
```

**Expected message:**
```json
{
  "type": "match-update",
  "data": {
    "scoreboard_data": {
      "id": 67,
      "show_team_names": false
      // Note: Only changed scoreboard field!
    }
  }
}
```

**Message size:** ~100-300B (partial scoreboard data)

---

## Success Criteria

### WebSocket Messages

- [ ] Initial load message: **full data** (5-10KB)
- [ ] Matchdata update message: **full match data with all relations** (3-8KB)
- [ ] Scoreboard update message: **included in match-update** (via match-update type)
- [ ] Clock updates: **partial clock data** (200-400B each)
- [ ] Event updates: **full events list** (500-2000B)
- [ ] Statistics updates: **full statistics** (1-2KB)

### Frontend Behavior

- [ ] UI updates **immediately** on backend changes
- [ ] No **page reload** required
- [ ] **ScoreboardViewComponent** displays updated data
- [ ] **ScoreboardAdminComponent** displays updated data (verify)

### Performance

- [ ] Update latency < **100ms** (measure in Network tab - includes full data fetch)
- [ ] Database queries for full match data on each update (expected behavior)
- [ ] Match-update messages are **~50-60%** of initial load size (includes all relations but omits clocks/stats)

---

## Troubleshooting

### Issue: No WebSocket messages received

**Check:**
1. Is backend running? (`curl http://localhost:8000/health`)
2. Is WebSocket connected? (Network tab shows connection)
3. Any errors in Console tab?

### Issue: Frontend not updating

**Check:**
1. Verify `matchDataPartial` signal is updated (Console: `wsService.matchDataPartial()`)
2. Check component effects are registered (source code: `wsMatchDataPartialEffect`)
3. Look for merge effect errors in Console

### Issue: Still seeing full data on updates

**Possible cause:** Backend migration not applied

**Fix:**
```bash
cd ../statsboards-backend
alembic upgrade head
```

---

## Expected Network Timeline

```
[Initial Load]  0ms      -> type: initial-load, size: 8.5KB
[Update]        5.2s     -> type: match-update, size: 5.2KB (full match data)
[Clock]         12.8s    -> type: gameclock-update, size: 350B
[Clock]         15.1s    -> type: playclock-update, size: 320B
[Update]        20.1s    -> type: match-update, size: 5.2KB (full match data)
[Event]         25.5s    -> type: event-update, size: 800B
[Stats]         25.5s    -> type: statistics-update, size: 1.5KB
```

---

## Related Files

### Frontend

- `src/app/core/services/websocket.service.ts:98-100` - Partial signals
- `src/app/core/services/websocket.service.ts:413-456` - Message handler
- `src/app/features/scoreboard/pages/view/scoreboard-view.component.ts:184-212` - Merge effects
- `src/app/features/scoreboard/pages/admin/scoreboard-admin.component.ts:116-146` - Verify admin component

### Backend

- `src/utils/websocket/websocket_manager.py:132-160` - Match data listener (fetches full data)
- `alembic/versions/2026_01_27_1000-stab147_matchdata.py` - Matchdata trigger
- `alembic/versions/2026_01_27_1005-stab148_scoreboard.py` - Scoreboard trigger
- `tests/test_websocket/test_match_data_listener.py` - Tests for match data listener
- `src/websocket/match_handler.py:160-205` - Process match data

---

## References

- **Linear Issue:** [STAF-208](https://linear.app/statsboard/issue/STAF-208)
- **Backend Issue:** [STAB-147](https://linear.app/statsboard/issue/STAB-147) - Optimized matchdata trigger
- **Backend Issue:** [STAB-148](https://linear.app/statsboard/issue/STAB-148) - Optimized scoreboard trigger
- **Backend Issue:** [STAB-149](https://linear.app/statsboard/issue/STAB-149) - Match data listener with full data fetch
- **Documentation:** [WEBSOCKET_DATA_FLOW.md](./WEBSOCKET_DATA_FLOW.md) - Complete WebSocket data flow documentation
