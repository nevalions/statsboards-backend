# AGENTS.md

This file provides guidance for agentic coding assistants working in this repository.

## Essential Commands

### Testing

```bash
# Run all tests
poetry run pytest

# Run a single test file
poetry run pytest tests/test_db_services/test_tournament_service.py

# Run a specific test function
poetry run pytest tests/test_db_services/test_tournament_service.py::TestTournamentServiceDB::test_create_tournament_with_relations

# Run tests with coverage
poetry run pytest --cov=src

# Run async tests only
poetry run pytest tests/ -k "async"
```

### Code Quality

```bash
# Format code with Black
poetry run black src/ tests/

# Lint with PyLint
poetry run pylint src/
```

### Database

```bash
# Generate migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Downgrade migration
poetry run alembic downgrade -1
```

### Running the Application

```bash
# Development server with hot reload
poetry run python src/runserver.py

# Production server
poetry run python src/run_prod_server.py
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

- Use try/except blocks for database operations
- Log errors with `exc_info=True` for stack traces
- Raise `HTTPException` with appropriate status codes:
  - 404: Resource not found
  - 409: Conflict/error in operation
  - 400: Invalid input
- Always return meaningful error messages in `detail` field

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
