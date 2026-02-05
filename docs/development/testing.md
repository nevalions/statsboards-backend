# Testing

## Guidelines

- Use `@pytest.mark.asyncio` for async test classes
- Use fixtures from `tests/fixtures.py` for common setup
- Use factory classes from `tests/factories.py` for test data
- Write descriptive docstrings for test methods
- Use helper functions from `tests/testhelpers.py` for assertions
- Test both success and error paths
- Never suppress exceptions in fixtures
- In test fixtures, use `flush()` instead of `commit()` to avoid deadlocks

## Test Suite Status

For current timing/coverage status, see `AGENTS.md` and `docs/TEST_COVERAGE_PLAN.md`.

## Testing Enhancements

### Test Factories with SubFactory

- Basic factories: `SportFactoryAny`, `SeasonFactoryAny`, `TournamentFactory`, etc.
- Enhanced factories with relations: `TournamentFactoryWithRelations`, `TeamFactoryWithRelations`, etc.
- Example: `TournamentFactoryWithRelations.build()` creates sport, season, and tournament

### Property-Based Testing

- Tests with Hypothesis for edge cases across wide input ranges
- Run with: `pytest tests/test_property_based.py`

### E2E Integration Tests

- Complete workflows across multiple services and endpoints
- Run with: `pytest tests/test_e2e.py -m e2e`

### Utils and Logging Tests

- Tests for `src.logging_config`
- Tests for `src.utils.websocket.websocket_manager`
- Run with: `pytest tests/test_utils.py`

### Test Markers

- `@pytest.mark.integration` - hits real websites or production folders
- `@pytest.mark.e2e` - end-to-end tests
- `@pytest.mark.slow` - slow-running tests

### Understanding Test Markers

Integration tests should pre-check external dependencies to avoid flaky failures:

```python
async def is_website_reachable(url: str, timeout: int = 5) -> bool:
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.head(url, allow_redirects=True) as response:
                return response.status < 500
    except Exception:
        return False

@pytest.mark.asyncio
async def test_external_service_integration(self):
    if not await is_website_reachable("https://example.com"):
        pytest.skip("External website not reachable, skipping integration test")
```

## Coverage

- Config: `.coveragerc`
- HTML report: `pytest --cov=src --cov-report=html`
- Terminal report: `pytest --cov=src --cov-report=term-missing`
- XML report: `pytest --cov=src --cov-report=xml`

## PostgreSQL Requirement

Do not use SQLite for tests. PostgreSQL is required because:

- WebSocket functionality uses LISTEN/NOTIFY
- Tests rely on PostgreSQL-specific data types and functions
- Connection pooling and transaction isolation behaviors must match production

## PostgreSQL Test Performance Optimization

Current optimizations:

- Database echo disabled in test fixtures
- Transaction rollback per test
- No Alembic migrations: direct table creation with file-based lock coordination
- Parallel test execution with pytest-xdist: `-n 8` across 8 databases
- PostgreSQL performance tuning in `docker-compose.test-db-only.yml`
- Worker-specific lock files (`/tmp/test_db_tables_setup_{db_name}.lock`) coordinate table creation
- Worker distribution: gw0 → test_db, gw1 → test_db2, gw2 → test_db3, gw3 → test_db4, gw4 → test_db5, gw5 → test_db6, gw6 → test_db7, gw7 → test_db8

Test fixtures use `test_mode=True` in the Database class, which replaces `commit()` with `flush()` in CRUDMixin:

```python
database = Database(test_db_url, echo=False, test_mode=True)
```

When writing direct session code in test fixtures:

```python
async with test_db.get_session_maker()() as db_session:
    role = RoleDB(name="test_role", description="Test role")
    db_session.add(role)
    await db_session.flush()
```

## Minimal Test App Fixtures

Tests can use minimal test app fixtures that only initialize required routers.

### Router Groups

| Group | Routers Included | Count | Use For |
|-------|-----------------|--------|----------|
| `CORE` | health, auth, global_settings, users, roles | 5 | Minimal infrastructure tests |
| `SPORT` | CORE + sports, teams, tournaments, seasons, team_tournament | 10 | Sport/team/tournament tests |
| `PLAYER` | CORE + players, persons, positions, player_match, player_team_tournament | 10 | Player/person/position tests |
| `MATCH` | CORE + match (3), matchdata, gameclock, playclock, scoreboard, football_events | 13 | Match/clock/scoreboard tests |
| `SPONSOR` | CORE + sponsors, sponsor_lines, sponsor_sponsor_line_connection | 8 | Sponsor tests |

### Available Fixtures

| Fixture | Description | Routers |
|---------|-------------|----------|
| `client` | Full app with all routers | ALL |
| `client_minimal` | Minimal app with core routers only | 5 |
| `client_sport` | App with sport-related routers | 10 |
| `client_player` | App with player-related routers | 10 |
| `client_match` | App with match-related routers | 13 |
| `client_sponsor` | App with sponsor-related routers | 8 |

### Usage Examples

```python
async def test_create_sport(self, client_sport, test_db):
    response = await client_sport.post("/api/sports/", json={...})

async def test_start_gameclock(self, client_match, test_db):
    response = await client_match.put(f"/api/matchdata/{id}/gameclock/running/")
```

### Factory Function

```python
from tests.fixtures.app_fixtures import create_test_app, CORE_ROUTERS, MATCH_ROUTERS

custom_app = create_test_app([CORE_ROUTERS, MATCH_ROUTERS])
```

### Choosing the Right Fixture

1. Check which endpoints your test uses
2. Map endpoints to router groups
3. Use the corresponding `client_*` fixture
4. If in doubt, start with `client` and optimize later
