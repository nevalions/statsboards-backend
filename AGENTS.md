# AGENTS.md

This file provides guidance for agentic coding assistants working in this repository.

## Overview

For detailed development guidelines, coding standards, and best practices, see **[DEVELOPMENT_GUIDELINES.md](docs/DEVELOPMENT_GUIDELINES.md)**.

This document serves as a quick reference for common operations and links to the comprehensive guidelines.

## Frontend

The main frontend for this project is **[frontend-angular-signals](../frontend-angular-signals/)**, located in the parent directory (`../`).

**Permissions:** You have read access to the frontend folder and can read files from it without asking permission. Edit access is denied.

## Quick Reference

### Essential Commands

**Testing:**
```bash
# Run fast tests with 8 workers (recommended, restarts DB first)
./run-tests.sh

# Run fast tests (parallel with 8 workers, skips slow/integration tests)
pytest

# Run ALL tests including slow tests
pytest -m ""

# Run only slow tests
pytest -m "slow"

# Run tests sequentially (for debugging)
pytest -n 0

# Run with coverage
./run-tests.sh --cov=src --cov-report=html
```

**Code Quality:**
```bash
# Lint with Ruff
source venv/bin/activate && ruff check src/ tests/

# Auto-fix Ruff issues
source venv/bin/activate && ruff check --fix src/ tests/
```

**Database:**
```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade migration
alembic downgrade -1
```

### Key Documents

- **[DEVELOPMENT_GUIDELINES.md](docs/DEVELOPMENT_GUIDELINES.md)** - Comprehensive development guide with all coding standards, patterns, and best practices
- **[SERVICE_LAYER_DECOUPLING.md](docs/SERVICE_LAYER_DECOUPLING.md)** - Service layer architecture and dependency injection patterns
- **[CONFIGURATION_VALIDATION.md](docs/CONFIGURATION_VALIDATION.md)** - Configuration settings and validation details

### Test Suite Status

Fast tests: 1430 tests pass in ~16s (8 workers). Full suite: ~1523 tests in ~90s. Tests use:
- Transactional rollback for isolation
- 8 parallel databases (test_db, test_db2, test_db3, test_db4, test_db5, test_db6, test_db7, test_db8) distributed across 8 workers
- Worker-specific lock files for safe table creation

**Worker distribution:**
- gw0 → test_db
- gw1 → test_db2
- gw2 → test_db3
- gw3 → test_db4
- gw4 → test_db5
- gw5 → test_db6
- gw6 → test_db7
- gw7 → test_db8

**Testing Recommendations:**
- Use `./run-tests.sh` for most development work (restarts DB before running tests)
- For absolute stability (CI, critical debugging), use `pytest -n 0` (sequential)
- Parallel tests (8 workers) are now stable with no race conditions or flakiness

**Coverage:** ~76% overall (76.32% as of 2026-01-30). Coverage percentages below should be verified after running tests with coverage.

**Modules with low coverage (<50%):**
- `src/player_team_tournament/views.py` (44.32%) - Player-team-tournament API endpoints
- `src/playclocks/views.py` (46.22%) - Play clock API endpoints
- `src/player/views.py` (50.94%) - Player API endpoints (7 new endpoint tests added 2026-01-30)
- `src/player_match/views.py` (50.34%) - Player-match API endpoints

**Note:** On 2026-01-31, 26 additional tests were added for error handling and edge cases in playclocks, player_team_tournament, and player_match views. Run `./run-tests.sh --cov=src` to verify updated coverage.

**Recently improved coverage (2026-01-30):**
- `src/websocket/match_handler.py` - Added 25 tests for process_data_websocket, error handling, WebSocket state validation, and connection closed scenarios
- `src/pars_eesl/pars_tournament.py` - Added 5 tests for error handling, multiple weeks parsing, color extraction errors, and empty scores
- `src/player/views.py` - Added 7 endpoint tests for get_player_by_eesl_id, person_by_player_id, remove_person_from_sport, and update_player

**Recently improved coverage (2026-01-31):**
- `src/playclocks/views.py` - Added 13 tests for error handling (IntegrityError, SQLAlchemyError, general exceptions) and empty result scenarios
- `src/player_team_tournament/views.py` - Added 13 tests for exception handling, empty results, and edge cases
- `src/player_match/views.py` - Added 3 tests for exception handling and parsing scenarios

**Recently improved coverage (2026-02-05):**
- `src/matches/stats_websocket_handler.py` - Added 11 tests for exception handling, client exclusion, WebSocket disconnect, malformed JSON, invalid timestamps, and full connection lifecycle
- `src/pars_eesl/pars_match.py` - Added 15 tests for parsing match data, player data, edge cases, and error handling

**Modules with high coverage (>90%):**
- Most schema files have 100% coverage
- `src/helpers/file_service.py` (97.46%)
- `src/helpers/download_service.py` (95.05%)
- `src/helpers/upload_service.py` (96.34%)
- `src/seasons/db_services.py` (94.74%)
- `src/sports/views.py` (95.77%)
- Many core utilities and database services

**Important:** When writing test fixtures, use `flush()` instead of `commit()` to avoid deadlocks during parallel test execution. The outer test fixture handles rollback automatically.

For detailed test information and recent fixes, see the [Test Suite Status](docs/DEVELOPMENT_GUIDELINES.md#test-suite-status) section in DEVELOPMENT_GUIDELINES.md.

### Search Testing Guidelines

Search functionality has been refactored to use shared `SearchPaginationMixin` for consistency. See the [Search Testing Guidelines](docs/DEVELOPMENT_GUIDELINES.md#search-testing-guidelines) section in DEVELOPMENT_GUIDELINES.md for details.

### Tooling and Testing

| Tool | Purpose | Command |
|------|----------|----------|
| pytest | Test runner | `pytest` |
 | pytest-xdist | Parallel test execution (8 workers using 8 databases) | `pytest -n 8` |
| pytest-timeout | Test timeout to prevent hung tests | Default 30s timeout |
| run-tests.sh | Run tests with DB restart (recommended) | `./run-tests.sh` |
| pytest-cov | Coverage reporting | `./run-tests.sh --cov=src` |
| Hypothesis | Property-based testing | `pytest tests/test_property_based.py` |
| Ruff | Linting | `ruff check src/ tests/` |
| Alembic | Database migrations | `alembic upgrade head` |

### Test Markers

- `@pytest.mark.integration` - Tests that hit external websites or write to production folders
- `@pytest.mark.e2e` - End-to-end integration tests
- `@pytest.mark.slow` - Slow-running tests (skipped by default, run with `-m slow` or `-m ""` to include)
- `@pytest.mark.property` - Property-based tests
- `@pytest.mark.timeout(N)` - Override default timeout for specific tests (in seconds)

### Important Notes

**Note:** Do not add AGENTS.md to README.md - this file is for development reference only.

**Note:** All commits must be by linroot with email nevalions@gmail.com

**Note:** When you need to search docs, use `context7` tools.

**Note:** Tests use transactional rollback for isolation. Always use `flush()` instead of `commit()` in test fixtures to avoid deadlocks during parallel execution.

**Note:** Parallel testing with 8 workers on 8 databases provides optimal isolation (1 worker per database) and is now stable with no race conditions or flakiness. The `run-tests.sh` script includes a 3-second delay after database ready check to ensure workers have time to initialize tables across all 8 databases.

**Note:** pytest-timeout is configured with a 30s default timeout (thread method) to prevent hung tests from blocking workers. Integration tests that legitimately take longer should be marked with `@pytest.mark.timeout(N)` where N is the timeout in seconds. Typical timeouts: unit tests 10s, database tests 30s (default), WebSocket tests 60s, integration tests 120s.

### Workflow References

See docs/DEVELOPMENT_GUIDELINES.md for:
- Code style guidelines and naming conventions
- Service layer and router patterns
- Model patterns and relationship types
- Error handling patterns
- Database operations and relationship loading
- Search implementation guidelines
- WebSocket and real-time patterns
- Configuration validation details
