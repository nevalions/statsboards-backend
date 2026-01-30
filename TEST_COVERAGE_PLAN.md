# Test Coverage Improvement Plan

**Generated:** 2026-01-18
**Current Coverage:** 76.32% overall (as of 2026-01-30)
**Recent Updates:**
- 2026-01-30: Added 37 new tests across 3 files (match_handler: 25, pars_tournament: 5, player views: 7)

## Priority 1 - Critical gaps (<30%)

### ~~1. `src/websocket/match_handler.py` - 11.43% (133/153 missing)~~ ✅ COMPLETED
- **Impact:** Core WebSocket functionality
- **Missing lines:** 22-71, 76-85, 90-146, 149-180, 183-215, 220-252, 259-284
- **Type:** Integration tests for WebSocket message handling
- **Updated:** 2026-01-19 - Added 22 integration tests (86.29% coverage)

### 2. `src/player_match/views.py` - 28.98% (150/227 missing)
- **Impact:** REST endpoint coverage
- **Missing lines:** 55-59, 86-87, 104, 109-110, 119-122, 129-132, 139-142, 149-152, 189-524, 542-544, 548-580, 583-584
- **Type:** API endpoint tests

### 3. `src/player/db_services.py` - 30.14% (136/214 missing)
- **Impact:** Business logic layer
- **Missing lines:** 87-89, 134, 136, 199-277, 302-390, 417-499, 508-617, 652-721, 765
- **Type:** Service layer tests with DB

## Priority 2 - Significant gaps (30-50%)

### 4. `src/pars_eesl/parse_player_team_tournament.py` - 28.57%
- **Impact:** EESL data parsing
- **Type:** Parser tests with mock data

### 5. `src/pars_eesl/pars_tournament.py` - 42.29%
- **Impact:** Tournament data parsing
- **Type:** Parser tests with mock data

### 6. `src/matches/crud_router.py` - 49.64% (125/252 missing)
- **Impact:** CRUD operations for matches
- **Type:** Router tests with DB

### 7. `src/matches/db_services.py` - 47.95% (112/247 missing)
- **Impact:** Match business logic
- **Type:** Service layer tests with DB

### 8. `src/core/models/mixins/relationship_mixin.py` - 47.32%
- **Impact:** Database relationship management
- **Type:** Model/relationship tests

## Priority 3 - Moderate gaps (50-65%)

### 9. `src/player_team_tournament/views.py` - 43.45%
- **Impact:** Player-tournament-tournament relationships API
- **Type:** API endpoint tests

### 10. `src/teams/views.py` - 43.17%
- **Impact:** Teams API endpoints
- **Type:** API endpoint tests

### 11. `src/teams/db_services.py` - 53.17%
- **Impact:** Teams business logic
- **Type:** Service layer tests with DB

### 12. `src/player_match/db_services.py` - 51.59%
- **Impact:** Player-match relationship management
- **Type:** Service layer tests with DB

## Notes

- **Excluded from coverage requirements:** Redis and SSE modules (as discussed)
- **Test command:** `pytest --cov=src --cov-report=term-missing --cov-report=html`
- **View HTML report:** `open htmlcov/index.html`
- **Parallel execution:** Uses 4 workers with 2 databases (test_db, test_db2)
