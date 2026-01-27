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

**After:** Backend sends enhanced notifications with actual row data
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
    // ... other fields
  }
}
```

Backend wraps this as:
```json
{
  "type": "match-update",
  "data": {
    "match_data": {
      "id": 67,
      "score_team_a": 7,
      "score_team_b": 3,
      // ...
    }
  }
}
```

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

### 5. Observe Partial Update in DevTools

**Expected message:**
```json
{
  "type": "match-update",
  "data": {
    "match_data": {
      "id": 67,
      "score_team_a": 10,
      "qtr": "Q3"
      // Note: Only changed fields, not full row!
    }
  }
}
```

**Message size:** ~100-500B (partial data)

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
- [ ] Matchdata update message: **partial match_data** (100-500B)
- [ ] Scoreboard update message: **partial scoreboard_data** (100-300B)
- [ ] Clock updates: **full clock data** (existing behavior)

### Frontend Behavior

- [ ] UI updates **immediately** on backend changes
- [ ] No **page reload** required
- [ ] **ScoreboardViewComponent** displays updated data
- [ ] **ScoreboardAdminComponent** displays updated data (verify)

### Performance

- [ ] Update latency < **50ms** (measure in Network tab)
- [ ] No database queries logged after initial load
- [ ] Partial messages are **10-100x smaller** than initial load

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
[Update]        5.2s     -> type: match-update, data: match_data, size: 180B
[Update]        12.8s    -> type: match-update, data: scoreboard_data, size: 120B
[Update]        20.1s    -> type: match-update, data: match_data, size: 180B
[Clock]         28.5s    -> type: gameclock-update, size: 350B
```

---

## Related Files

### Frontend

- `src/app/core/services/websocket.service.ts:98-100` - Partial signals
- `src/app/core/services/websocket.service.ts:413-456` - Message handler
- `src/app/features/scoreboard/pages/view/scoreboard-view.component.ts:184-212` - Merge effects
- `src/app/features/scoreboard/pages/admin/scoreboard-admin.component.ts:116-146` - Verify admin component

### Backend

- `alembic/versions/2026_01_27_1000-stab147_matchdata.py` - Matchdata trigger
- `alembic/versions/2026_01_27_1005-stab148_scoreboard.py` - Scoreboard trigger
- `src/websocket/match_handler.py:160-205` - Process match data

---

## References

- **Linear Issue:** [STAF-208](https://linear.app/statsboard/issue/STAF-208)
- **Backend Issue:** [STAB-147](https://linear.app/statsboard/issue/STAB-147)
- **Backend Issue:** [STAB-148](https://linear.app/statsboard/issue/STAB-148)
