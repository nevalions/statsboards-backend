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
# Run all tests
pytest

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
```

**Note:** The `pytest.ini` file includes performance optimizations (`-x -v --tb=short`) for faster test execution:
- `-x`: Stop on first failure
- `-v`: Verbose output
- `--tb=short`: Shortened traceback format
- `log_cli=false`: Live logs disabled by default (use `-o log_cli=true` to enable for debugging)

**Note:** Database echo is disabled in test fixtures for faster test execution.

**Note:** Ensure environment variables point to test database

### Code Quality

```bash
# Format code with Black
black src/ tests/

# Lint with PyLint
pylint src/
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

**Important:** Do NOT use SQLite for tests. Tests must use PostgreSQL because:

- WebSocket functionality requires PostgreSQL LISTEN/NOTIFY features
- Tests use PostgreSQL-specific data types and functions
- Full compatibility with production database behavior is required
- Connection pooling and transaction isolation behavior differs

### PostgreSQL Test Performance Optimization

Current optimizations already implemented:

- Database echo disabled in test fixtures (tests/conftest.py:22)
- Transaction rollback per test (fast cleanup without table drops)
- No Alembic migrations (direct table creation)

Additional optimization opportunities:

- Session-scoped database engine (create tables once per session)
- PostgreSQL connection pool tuning (pool_size, max_overflow)
- PostgreSQL performance tuning (fsync=off, synchronous_commit=off)
- Parallel test execution with pytest-xdist (`-n auto`)
- Docker PostgreSQL performance settings in docker-compose.test-db-only.yml

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

**Note**: Do not add AGENTS.md to README.md - this file is for development reference only.
**Note**: all commits must be by linroot with email nevalions@gmail.com
