# AGENTS.md

This file provides guidance for agentic coding assistants working in this repository.

## Essential Commands

### Prerequisites

Before running any commands, ensure the virtual environment is activated:

```bash
# activate venv directly (if using venv)
source venv/bin/activate
```

### Testing

**Important: When running in agent mode, use non-verbose until error or fail catched**

```bash
docker-compose -f docker-compose.test-db-only.yml up -d && source venv/bin/activate && pytest 2>&1 | tail -20
```

**Important: Before running tests, start test database:**

```bash
# Start test database (for running selective tests locally)
docker-compose -f docker-compose.test-db-only.yml up -d
```

Then run tests:

```bash
# Run all tests (parallel by default with pytest-xdist)
pytest

# Run tests sequentially (for debugging)
pytest -n 0

# Run tests for specific directory
pytest tests/test_db_services/
pytest tests/test_views/

# Run a single test file
pytest tests/test_db_services/test_tournament_service.py

# Run a specific test function
pytest tests/test_db_services/test_tournament_service.py::TestTournamentServiceDB::test_create_tournament_with_relations

# Run a specific test with live logs enabled
pytest tests/test_db_services/test_tournament_service.py::TestTournamentServiceDB::test_create_tournament_with_relations -o log_cli=true

# Run tests with coverage
pytest --cov=src

# Run async tests only
pytest tests/ -k "async"

# Run tests with coverage (HTML report)
pytest --cov=src --cov-report=html

# Run tests with coverage (terminal report)
pytest --cov=src --cov-report=term-missing

# Run tests with coverage (XML report for CI/CD)
pytest --cov=src --cov-report=xml

# Run property-based tests
pytest tests/test_property_based.py

# Run performance benchmarks
pytest tests/test_benchmarks.py -m benchmark

# Run E2E integration tests
pytest tests/test_e2e.py -m e2e

# Run utils tests
pytest tests/test_utils.py

# Run tests in parallel with pytest-xdist
pytest -n auto

# Run tests matching a specific marker
pytest -m integration
pytest -m benchmark
pytest -m e2e
pytest -m "not slow"

# Run benchmarks with comparison to baseline
pytest tests/test_benchmarks.py -m benchmark --benchmark-only --benchmark-compare

# Run specific test types
pytest -k "property"
pytest -k "benchmark"
pytest -k "e2e"
```

**Note:** The `pytest.ini` file includes performance optimizations (`-x --tb=short -n auto`) for faster test execution:

- `-x`: Stop on first failure
- `--tb=short`: Shortened traceback format
- `-n auto`: Run tests in parallel using pytest-xdist (uses all available CPU cores)
- `log_cli=false`: Live logs disabled by default (use `-o log_cli=true` to enable for debugging)
- Session-scoped database engine: Tables created once per session instead of per-test
- Transaction rollback per test: Fast cleanup without table drops

**Note:** Database echo is disabled in test fixtures for faster test execution.

**Note:** Ensure environment variables point to test database

### Code Quality

```bash
# Lint with Ruff
source venv/bin/activate && ruff check src/ tests/

# Auto-fix Ruff issues where possible
source venv/bin/activate && ruff check --fix src/ tests/
```

### Database

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade migration
alembic downgrade -1
```

### Running the Application

```bash
# Development server with hot reload
python src/runserver.py

# Production server
python src/run_prod_server.py
```

### Configuration Validation

```bash
# Validate configuration before starting application
python validate_config.py

# Configuration validation also runs automatically on application startup
```

## Code Style Guidelines

### Import Organization

- Standard library imports first
- Third-party imports second
- Local application imports third
- Use `from typing import` for type hints at the top
- Use relative imports within domain modules (e.g., `from .schemas import ...`)
- Use absolute imports for cross-domain imports (e.g., `from src.core.models import ...`)

### Type Hints

- Use Python 3.11+ type hint syntax: `str | None` instead of `Optional[str]`
- Always annotate function parameters and return types
- Use `Annotated` for Pydantic field validation: `Annotated[str, Path(max_length=50)]`
- Use `TYPE_CHECKING` for circular import dependencies in models

### Naming Conventions

- **Classes**: PascalCase with descriptive suffixes (e.g., `TeamServiceDB`, `TeamSchema`, `TeamAPIRouter`)
- **Functions**: snake_case with descriptive names (e.g., `create_or_update_team`, `get_team_by_eesl_id`)
- **Variables**: snake_case (e.g., `team_id`, `tournament_id`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `ITEM = "TEAM"`)
- **Private methods**: Prefix with underscore if needed (e.g., `_validate_data`)

### Service Layer Pattern

- All service classes inherit from `BaseServiceDB`
- Initialize with database dependency: `super().__init__(database, TeamDB)`
- Use `self.logger` for structured logging with consistent format
- Return database model objects, not dictionaries
- Raise `HTTPException` for client-facing errors
- Use `async/await` for all database operations
- **Use Service Registry for cross-service dependencies**:
  - Never directly import and instantiate other services
  - Access dependencies through `self.service_registry.get("service_name")`
  - Example: `team_service = self.service_registry.get("team")`
  - Registry is lazily initialized to avoid order issues
  - See `SERVICE_LAYER_DECOUPLING.md` for full documentation

### Router Pattern

- Inherit from `BaseRouter[SchemaType, CreateSchemaType, UpdateSchemaType]`
- Initialize with prefix and tags: `super().__init__("/api/teams", ["teams"], service)`
- Add custom endpoints after calling `super().route()`
- Use descriptive endpoint function names with `_endpoint` suffix
- Return `object.__dict__` for responses to match schemas

### Schema Patterns

- Inheritance: `TeamSchemaBase` → `TeamSchemaCreate` → `TeamSchema`
- `TeamSchemaUpdate` should have all fields optional
- Add `model_config = ConfigDict(from_attributes=True)` to output schemas
- Use Pydantic `Annotated` for validation constraints
- Keep response models separate from request models

### Model Patterns

- Use `Mapped[type]` with `mapped_column()` for all columns
- Always set `nullable=True` for optional fields
- Use `default` and `server_default` for default values
- Define relationships with proper `back_populates`
- Use `TYPE_CHECKING` block for forward references
- Include `__table_args__ = {"extend_existing": True}` in all models

### Error Handling

**IMPORTANT**: Avoid generic `except Exception:` clauses. Use specific exception types for better debugging and error monitoring.

- Import custom exceptions from `src.core.exceptions`:
  - `ValidationError`: Data validation errors (400)
  - `NotFoundError`: Resource not found (404)
  - `DatabaseError`: Database operation failures (500)
  - `BusinessLogicError`: Business rule violations (422)
  - `ExternalServiceError`: External service failures (503)
  - `ConfigurationError`: Configuration issues (500)
  - `AuthenticationError`: Authentication failures (401)
  - `AuthorizationError`: Authorization failures (403)
  - `ConcurrencyError`: Race conditions (409)
  - `FileOperationError`: File operations (500)
  - `ParsingError`: Data parsing failures (400)

**PREFERRED**: Use `@handle_service_exceptions` decorator to eliminate boilerplate:

```python
from src.core.models import handle_service_exceptions

# For create/update operations (raise NotFoundError)
@handle_service_exceptions(item_name=ITEM, operation="creating")
async def create(self, item: TeamSchemaCreate) -> TeamDB:
    team = self.model(**item.model_dump())
    return await super().create(team)

# For fetch operations that return None on NotFound
@handle_service_exceptions(
    item_name=ITEM,
    operation="fetching players",
    return_value_on_not_found=[]
)
async def get_players_by_team_id(self, team_id: int) -> list[PlayerDB]:
    async with self.db.async_session() as session:
        stmt = select(PlayerDB).where(PlayerDB.team_id == team_id)
        results = await session.execute(stmt)
        return results.scalars().all()

# For fetch operations that raise NotFoundError
@handle_service_exceptions(
    item_name=ITEM,
    operation="fetching by ID",
    reraise_not_found=True
)
async def get_by_id(self, item_id: int) -> TeamDB:
    return await super().get_by_id(item_id)
```

- **MANUAL** try/except blocks should only be used for special cases:
  - Custom error handling that doesn't fit decorator pattern
  - Methods with complex exception handling logic
  - When you need to perform cleanup before re-raising

- For manual try/except, catch specific exceptions in this order:

  ```python
  try:
      # business logic
  except HTTPException:
      raise  # Re-raise HTTPExceptions
  except (IntegrityError, SQLAlchemyError) as ex:
      # Database errors
      self.logger.error(f"Database error: {ex}", exc_info=True)
      raise HTTPException(status_code=500, detail="Database error")
  except ValidationError as ex:
      # Validation errors
      self.logger.warning(f"Validation error: {ex}", exc_info=True)
      raise HTTPException(status_code=400, detail=str(ex))
  except (ValueError, KeyError, TypeError) as ex:
      # Data errors
      self.logger.warning(f"Data error: {ex}", exc_info=True)
      raise HTTPException(status_code=400, detail="Invalid data")
  except NotFoundError as ex:
      # Not found
      self.logger.info(f"Not found: {ex}", exc_info=True)
      raise HTTPException(status_code=404, detail=str(ex))
  except BusinessLogicError as ex:
      # Business logic errors
      self.logger.error(f"Business logic error: {ex}", exc_info=True)
      raise HTTPException(status_code=422, detail=str(ex))
  except Exception as ex:
      # Only for truly unexpected errors - should rarely trigger
      self.logger.critical(f"Unexpected error: {ex}", exc_info=True)
      raise HTTPException(status_code=500, detail="Internal server error")
  ```

- Raise `HTTPException` with appropriate status codes:
  - 400: Bad Request (ValidationError, ValueError, KeyError, TypeError)
  - 401: Unauthorized (AuthenticationError)
  - 403: Forbidden (AuthorizationError)
  - 404: Not Found (NotFoundError)
  - 409: Conflict (IntegrityError, ConcurrencyError)
  - 422: Unprocessable Entity (BusinessLogicError)
  - 500: Internal Server Error (DatabaseError, unexpected errors)
  - 503: Service Unavailable (ExternalServiceError, ConnectionError)
  - 504: Gateway Timeout (TimeoutError)
- Always return meaningful error messages in `detail` field
- Never use bare `except:` clauses
- Use appropriate logging levels:
  - `info`: NotFoundError
  - `warning`: ValidationError, ValueError, KeyError, TypeError
  - `error`: DatabaseError, BusinessLogicError
  - `critical`: Unexpected exceptions in final catch

### Logging

- Call `setup_logging()` at module level in services and routers
- Initialize logger with descriptive name: `get_logger("backend_logger_TeamServiceDB", self)`
- Use appropriate log levels:
  - `debug`: Detailed operation tracking
  - `info`: Significant operations (creates, updates)
  - `warning`: Expected but noteworthy situations
  - `error`: Unexpected errors with exceptions

### Testing

- Use `@pytest.mark.asyncio` for async test classes
- Use fixtures from `tests/fixtures.py` for common setup
- Use factory classes from `tests/factories.py` for test data
- Write descriptive docstrings for test methods
- Use helper functions from `tests/testhelpers.py` for assertions
- Test both success and error paths

### Testing Enhancements

The project includes several enhanced testing approaches:

**1. Test Factories with SubFactory** (`tests/factories.py`):

- Basic factories: `SportFactoryAny`, `SeasonFactoryAny`, `TournamentFactory`, etc.
- Enhanced factories with relations: `TournamentFactoryWithRelations`, `TeamFactoryWithRelations`, etc.
- Use SubFactory for automatic creation of related entities
- Example: `TournamentFactoryWithRelations.build()` creates sport, season, and tournament

**2. Performance Benchmarks** (`tests/test_benchmarks.py`):

- Benchmarked operations: CRUD operations, bulk inserts, complex queries
- Run with: `pytest tests/test_benchmarks.py -m benchmark`
- Compare with baseline: `pytest tests/test_benchmarks.py -m benchmark --benchmark-compare`
- Focuses on critical service operations

**3. Property-Based Testing** (`tests/test_property_based.py`):

- Tests with Hypothesis for edge cases across wide input ranges
- Critical functions tested: `safe_int_conversion`, `hex_to_rgb`, `convert_cyrillic_filename`, etc.
- Run with: `pytest tests/test_property_based.py`
- Catches edge cases traditional tests might miss

**4. E2E Integration Tests** (`tests/test_e2e.py`):

- Complete workflows across multiple services and endpoints
- Scenarios: tournament management, player management, error handling
- Run with: `pytest tests/test_e2e.py -m e2e`
- Tests realistic user journeys

**5. Utils and Logging Tests** (`tests/test_utils.py`):

- Tests for `src.logging_config` module: ContextFilter, ClassNameAdapter
- Tests for `src.utils.websocket.websocket_manager`: MatchDataWebSocketManager
- Run with: `pytest tests/test_utils.py`

**Test Markers** (defined in pytest.ini):

- `@pytest.mark.integration`: Tests that hit real websites or write to production folders
- `@pytest.mark.benchmark`: Performance benchmark tests
- `@pytest.mark.e2e`: End-to-end integration tests
- `@pytest.mark.slow`: Tests that take longer to run

**Test Coverage**:

- Configuration: `.coveragerc` for coverage settings
- HTML report: `pytest --cov=src --cov-report=html` (view in `htmlcov/index.html`)
- Terminal report: `pytest --cov=src --cov-report=term-missing`
- XML report: `pytest --cov=src --cov-report=xml` (for CI/CD)

**Important:** Do NOT use SQLite for tests. Tests must use PostgreSQL because:

- WebSocket functionality requires PostgreSQL LISTEN/NOTIFY features
- Tests use PostgreSQL-specific data types and functions
- Full compatibility with production database behavior is required
- Connection pooling and transaction isolation behavior differs

### PostgreSQL Test Performance Optimization

Current optimizations implemented:

- Database echo disabled in test fixtures (tests/conftest.py)
- Session-scoped database engine: Tables created once per session (major speedup)
- Transaction rollback per test: Fast cleanup without table drops
- No Alembic migrations: Direct table creation
- Parallel test execution with pytest-xdist: `-n auto` runs tests on all CPU cores
- PostgreSQL performance tuning in docker-compose.test-db-only.yml:
  - fsync=off, synchronous_commit=off, full_page_writes=off
  - wal_level=minimal, max_wal_senders=0
  - autovacuum=off, track_functions=none, track_counts=off
  - tmpfs for PostgreSQL data (in-memory storage)

### File Structure Per Domain

Each domain module must contain:

- `schemas.py`: Pydantic models for API contracts
- `db_services.py`: Service class inheriting from `BaseServiceDB`
- `views.py`: Router class inheriting from `BaseRouter`
- `__init__.py`: Exports the router as `api_<domain>_router`

### Database Operations

- Always use async context managers: `async with self.db.async_session() as session:`
- Use SQLAlchemy 2.0 select API: `select(Model).where(Model.field == value)`
- Use `session.execute(stmt)` and `results.scalars().all()` for queries
- Never commit manually in service methods - let BaseServiceDB handle it
- Use relationships defined in models rather than manual joins

### WebSocket and Real-time

- Use existing `ws_manager` for connection management
- Follow event notification patterns in existing modules
- Test connection handling and reconnection scenarios
- Use Redis pub/sub for scalable event distribution
- Always clean up connections on disconnect

### General Principles

- Follow existing patterns rather than creating new ones
- Keep functions focused and single-responsibility
- Prefer composition over inheritance
- Use type hints everywhere for better IDE support
- Write tests before or immediately after implementing features
- Always run lint and test commands before considering a task complete
- Never hardcode credentials or secrets - use environment variables
- Use Pydantic Settings for configuration in `src/core/config.py`

### Configuration Validation

The application includes comprehensive configuration validation that runs automatically on startup:

- **Database Settings Validation**:
  - Validates required fields (host, user, password, name) are not empty
  - Validates port is between 1 and 65535
  - Validates connection strings are valid
  - Main database validation is skipped when `TESTING` environment variable is set

- **Application Settings Validation**:
  - Validates CORS origins format (must start with http://, https://, or \*)
  - Validates SSL files: both SSL_KEYFILE and SSL_CERTFILE must be provided together or neither

- **Path Validation**:
  - Required paths: static_main_path, uploads_path (must exist and be readable)
  - Optional paths: template_path, static_path, SSL files (logged as warnings if missing)

- **Database Connection Validation**:
  - Tests basic database connectivity
  - Logs PostgreSQL version
  - Logs current database name
  - Logs current database user
  - Runs automatically on application startup via FastAPI lifespan

Run `python validate_config.py` to manually validate configuration before starting the application.

See `CONFIGURATION_VALIDATION.md` for complete documentation.

## Testing Enhancement Summary

The project has been enhanced with comprehensive testing capabilities:

### 1. Coverage Reporting

- **pytest-cov** added for code coverage tracking
- **.coveragerc** configuration with proper exclusions
- HTML, terminal, and XML report formats supported
- Run with: `pytest --cov=src --cov-report=html`

### 2. Performance Benchmarking

- **pytest-benchmark** for measuring critical operation performance
- Benchmark tests in `tests/test_benchmarks.py`
- Tests CRUD operations, bulk inserts, and complex queries
- Baseline comparison support for performance regression detection
- Run with: `pytest tests/test_benchmarks.py -m benchmark`

### 3. Property-Based Testing

- **Hypothesis** for testing across wide input ranges
- Property-based tests in `tests/test_property_based.py`
- Tests critical utility functions for edge cases
- Validates invariants and properties that should always hold true
- Run with: `pytest tests/test_property_based.py`

### 4. Enhanced Test Factories

- **SubFactory** support for automatic related entity creation
- New factories: `TournamentFactoryWithRelations`, `TeamFactoryWithRelations`, etc.
- Simplifies test setup for complex scenarios
- Reduces test code duplication

### 5. E2E Integration Tests

- End-to-end tests in `tests/test_e2e.py`
- Tests complete workflows across multiple services and endpoints
- Validates realistic user scenarios
- Tests error handling and cascade delete behaviors
- Run with: `pytest tests/test_e2e.py -m e2e`

### 6. Utils and Logging Tests

- Tests for `src.logging_config`: ContextFilter, ClassNameAdapter
- Tests for `src.utils.websocket.websocket_manager`: MatchDataWebSocketManager
- Ensures core utilities work correctly
- Run with: `pytest tests/test_utils.py`

### Test Markers

- `@pytest.mark.integration`: Integration tests (external dependencies)
- `@pytest.mark.benchmark`: Performance benchmarks
- `@pytest.mark.e2e`: End-to-end integration tests
- `@pytest.mark.slow`: Slow-running tests
- `@pytest.mark.property`: Property-based tests

### Running Tests

```bash
# Coverage reports
pytest --cov=src --cov-report=html          # HTML report
pytest --cov=src --cov-report=term-missing    # Terminal report
pytest --cov=src --cov-report=xml            # CI/CD XML report

# Specialized test runs
pytest tests/test_benchmarks.py -m benchmark               # Benchmarks only
pytest tests/test_benchmarks.py -m benchmark --benchmark-compare  # Compare baseline
pytest tests/test_property_based.py                          # Property-based tests
pytest tests/test_e2e.py -m e2e                         # E2E tests
pytest tests/test_utils.py                                    # Utils tests

# By marker
pytest -m integration    # Integration tests only
pytest -m benchmark      # Benchmarks only
pytest -m e2e           # E2E tests only
pytest -m "not slow"    # Skip slow tests

# Parallel execution
pytest -n auto          # Run tests in parallel
```

## Test Suite Status

All 500+ tests are passing as of latest fixes. Key fixes applied:

### Recent Test Fixes

**test_player_match_views_helpers.py** (9 tests - all passing)

- Fixed wrong patch path for `uploads_path` in test mocking
- Updated `photo_files_exist` function signature to accept `str | None` for type safety

**test_utils.py** (16 tests - all passing)

- Fixed `test_setup_logging_creates_logs_dir` to properly mock module-level `logs_dir` variable
- Added `AsyncMock` for async operations in WebSocket manager tests
- Improved exception handling for connection failure tests

**test_views/test_websocket_views.py** (47 tests passing)

- Fixed import path for `MatchDataWebSocketManager` from incorrect `src.core.models.base` to correct `src.utils.websocket.websocket_manager`
- Marked integration test requiring real database connections with `@pytest.mark.integration`

**test_pars_integration.py** (5 tests - all passing with `-m integration`)

- Integration tests run correctly when marked with `@pytest.mark.integration`
- Tests hit real EESL website and write to production directories

**test_views/test_health_views.py** (3 tests - all passing)

- Tests were already working correctly

### Running All Tests

```bash
# Run all non-integration tests
pytest

# Run all tests including integration
pytest -m "not slow or integration"

# Run specific test files
pytest tests/test_player_match_views_helpers.py
pytest tests/test_utils.py
pytest tests/test_views/test_websocket_views.py
```

## GitHub workflow (this repo)

- Default repo: <OWNER>/<REPO> (use this unless user specifies otherwise)
- Branch naming:
  - feature: feat/<linear-id>-<slug>
  - bugfix: fix/<linear-id>-<slug>
  - chore: chore/<linear-id>-<slug>
- Pull requests:
  - Always link the Linear issue (e.g. STAB-8)
  - Include: summary, scope, testing, screenshots (frontend), migration notes (backend)
  - Ensure CI is green before requesting review
- Required checks (do not merge unless passing):
  - backend: pytest + typecheck + migrations (if applicable)
- Labels:
  - security findings → label `security`
  - refactor-only → label `refactor`
- Reviewers:
  - assign <TEAM/USERNAMES> if applicable

## Linear defaults

- Default Linear team is **StatsboardBack**.
- When creating/updating Linear issues, always use this team unless the user explicitly says otherwise.
- If a project is not specified, create the issue without assigning a project (do not guess).
- When making a plan, create:
  - 1 parent issue (epic)
  - child issues grouped by theme
- Always include: rule name(s), file paths, and a clear "Done when" checklist.

## Perplexity usage rules

- Use Perplexity MCP only for:
  - Current best practices
  - Standards, RFCs, security guidance
  - Tooling or framework updates
- Prefer local codebase and Context7 docs for implementation details.
- Summarize sources clearly when using Perplexity.

**Note**: Do not add AGENTS.md to README.md - this file is for development reference only.
**Note**: all commits must be by linroot with email nevalions@gmail.com
**Note**: When you need to search docs, use `context7` tools.
