# Development Guidelines

This document contains comprehensive development guidelines, coding standards, and best practices for the statsboards-backend project.

## Table of Contents

- [Essential Commands](#essential-commands)
- [Code Style Guidelines](#code-style-guidelines)
- [Error Handling](#error-handling)
- [Logging](#logging)
- [Testing](#testing)
- [Database Operations](#database-operations)
  - [Combined Pydantic Schemas](#combined-pydantic-schemas)
- [Search Implementation](#search-implementation)
- [Grouped Data Schemas and Career Endpoint Pattern](#grouped-data-schemas-and-career-endpoint-pattern)
- [Advanced Filtering Patterns](#advanced-filtering-patterns)
- [WebSocket and Real-time](#websocket-and-real-time)
- [User Ownership and Privacy](#user-ownership-and-privacy)
- [General Principles](#general-principles)
- [Configuration Validation](#configuration-validation)

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

**Important: Parallel tests now work correctly with 1465 tests passing in ~160s:**

```bash
  pytest -n 4  # Run tests in parallel with 4 workers (using 4 databases)
  pytest -n 0  # Run tests sequentially (for debugging)
  ```

The default pytest.ini configuration uses `-n 4` for parallel test execution. Database connection and deadlock issues have been resolved by:
- Using worker-specific lock files (`/tmp/test_db_tables_setup_{db_name}.lock`) to coordinate table creation across parallel workers
- Using `filelock` library (cross-platform, 30s timeout) for reliable file locking
- Lock scope fixed - entire database setup (tables + indexes + roles) inside lock to prevent race conditions
- Using 4 parallel databases (test_db, test_db2, test_db3, test_db4) distributed across 4 workers:
  - gw0 → test_db
  - gw1 → test_db2
  - gw2 → test_db3
  - gw3 → test_db4
- Using `test_mode=True` in Database class which replaces `commit()` with `flush()` in CRUDMixin to avoid PostgreSQL deadlocks
- Transactional rollback per test via the outer test fixture
- PostgreSQL health check using `pg_isready` (30s max wait, no fixed sleep delay)

**Note:** Tests run reliably in parallel with no ResourceWarnings, unclosed connection warnings, deadlocks, or race conditions.

### Understanding Test Markers

Tests in the suite use markers to categorize test types. All 1465 tests run by default, but markers allow selective execution when needed.

**Breakdown of Marked Tests:**

| Test File | Tests | Markers | Reason |
|------------|--------|----------|--------|
| `test_download_service.py` | 15 | `@pytest.mark.slow` | Slow download tests with retries |
| `test_pars_integration.py` | 5 | `@pytest.mark.integration` | Hits real EESL website |
| `test_websocket_views.py` | 22 | `@pytest.mark.slow` + `@pytest.mark.integration` | WebSocket connection tests |
| `test_match_stats_websocket_integration.py` | 4 | `@pytest.mark.integration` | WebSocket integration tests |
| **Total Marked** | **46** | - | - |

**Marker Definitions:**

- **`@pytest.mark.slow`**: Tests that take longer to run (websocket tests with connection setup, download service with retry logic)
- **`@pytest.mark.integration`**: Tests that:
  - Hit external websites (EESL integration)
  - Require real database connections beyond test fixtures
  - Use production-like endpoints

**Handling External Dependencies**

Integration tests that depend on external websites should include a pre-check to skip the test if the external service is not reachable. This prevents test failures due to network issues or service outages:

```python
async def is_website_reachable(url: str, timeout: int = 5) -> bool:
    """Check if website is reachable."""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.head(url, allow_redirects=True) as response:
                return response.status < 500
    except Exception:
        return False

@pytest.mark.asyncio
async def test_external_service_integration(self):
    """Test integration with external service."""
    if not await is_website_reachable("https://example.com"):
        pytest.skip("External website not reachable, skipping integration test")

    # Test code that depends on external service
```

**Running Selective Tests:**

```bash
# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow

# Run integration and slow tests together
pytest -m "integration or slow"

# Exclude slow tests only
pytest -m "not slow"

# Exclude integration tests only
pytest -m "not integration"

# Exclude both slow and integration tests
pytest -m "not integration and not slow"
```

All 1465 tests run by default with `pytest -n 4` in ~160s.

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

# Run E2E integration tests
pytest tests/test_e2e.py -m e2e

# Run utils tests
pytest tests/test_utils.py

# Run tests in parallel with pytest-xdist
pytest -n auto

# Run tests matching a specific marker
pytest -m integration
pytest -m e2e
pytest -m "not slow"

# Run specific test types
pytest -k "property"
pytest -k "e2e"

# Run tests with random order to detect order-dependent tests
pytest --random-order

# Run tests with random order using time-based seed
pytest --random-order --random-order-seed=time

# Re-run tests with same seed for reproducibility
pytest --random-order --random-order-seed=12345

# Run tests with random order using convenience script
./run-tests-random.sh
```

**Note:** The `pytest.ini` file includes performance optimizations (`-x --tb=short -n 4`) for faster test execution:

- `-x`: Stop on first failure
- `--tb=short`: Shortened traceback format
- `-n 4`: Run tests in parallel using pytest-xdist (uses 4 workers across 2 databases)
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

**Note:** Ruff is used for linting Python code only (`.py` files). Markdown documentation files (`.md`) are not linted with Ruff. Documentation should follow the project's writing conventions as outlined in this guide.

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

### Conditional Statements

- **Use match/case for 5+ elif chains**: Python 3.10+ match/case pattern matching improves readability for complex conditional logic
  ```python
  match value_type:
      case "string":
          return str(value)
      case "int":
          return int(value)
      case "bool":
          return bool(value)
      case _:
          return value
  ```

- **Keep if/elif for simple logic**: Use traditional if/elif chains for:
  - 2-4 conditional branches
  - Complex conditions with side effects
  - Type checking with isinstance()
  
- **Always include default case**: Use `case _:` as catch-all for match/case statements

- **Prefer dictionaries for key-value mappings**: For simple lookups, dictionaries are more efficient than match/case
  ```python
  months = {"января": "january", "февраля": "february"}
  return months.get(russian_month, None)
  ```

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

### Authorization Pattern

For endpoints requiring role-based access control, use the `require_roles` dependency:

```python
from src.auth.dependencies import require_roles
from typing import Annotated

@router.post("/api/roles/")
async def create_role_endpoint(
    role_data: RoleSchemaCreate,
    _: Annotated[RoleDB, Depends(require_roles("admin"))],
) -> RoleSchema:
    # User has admin role
    return await service.create(role_data)
```

**Key points:**
- Use `require_roles("role1", "role2")` for dependencies requiring specific roles
- Accepts multiple roles - user needs at least one of the specified roles
- Uses service registry database for consistency with other dependencies
- Returns the authenticated user object with roles loaded

**Example endpoints:**
```python
# Admin-only endpoints
@router.put("/api/roles/{item_id}/")
async def update_role(
    item_id: int,
    _: Annotated[RoleDB, Depends(require_roles("admin"))],
):
    return await service.update(item_id, update_data)

@router.delete("/id/{model_id}")
async def delete_role(
    model_id: int,
    _: Annotated[RoleDB, Depends(require_roles("admin"))],
):
    return await service.delete(model_id)

# Multiple roles allowed (admin OR moderator)
@router.put("/api/content/")
async def update_content(
    content_id: int,
    content: ContentSchemaUpdate,
    user: Annotated[UserDB, Depends(require_roles("admin", "moderator"))],
):
    # User has either admin or moderator role
    return await service.update(content_id, content, user)
```

**Note:** The `require_roles` dependency internally fetches user from service registry using `UserServiceDB.get_by_id_with_roles()`, ensuring consistent database access across the application.

### Schema Patterns

- Inheritance: `TeamSchemaBase` → `TeamSchemaCreate` → `TeamSchema`
- `TeamSchemaUpdate` should have all fields optional
- Add `model_config = ConfigDict(from_attributes=True)` to output schemas
- Use Pydantic `Annotated` for validation constraints
- Keep response models separate from request models
- Add `from __future__ import annotations` at the top of schema files to enable forward references without quotes (modern Python 3.7+ pattern)

#### Shared Base Classes (src/core/shared_schemas.py)

Use shared base classes to avoid duplication across schemas:

**SponsorFieldsBase** - For entities with sponsor relationships
```python
from src.core.shared_schemas import SponsorFieldsBase

class TeamSchemaBase(SponsorFieldsBase):
    # Inherits: sponsor_line_id, main_sponsor_id
    # Add entity-specific fields below
    title: str
    sport_id: int
```

**PrivacyFieldsBase** - For entities with privacy/ownership fields
```python
from src.core.shared_schemas import PrivacyFieldsBase

class TeamSchemaBase(SponsorFieldsBase, PrivacyFieldsBase):
    # Inherits: sponsor_line_id, main_sponsor_id, isprivate, user_id
    # Add entity-specific fields below
    title: str
    sport_id: int
```

**PlayerTeamTournamentBaseFields** and **PlayerTeamTournamentWithTitles** - For player-team-tournament relationships
```python
from src.core.shared_schemas import PlayerTeamTournamentBaseFields, PlayerTeamTournamentWithTitles

class PlayerTeamTournamentWithDetailsSchema(PlayerTeamTournamentBaseFields):
    id: int
    first_name: str | None = None
    second_name: str | None = None
```

### Model Patterns

- Use `Mapped[type]` with `mapped_column()` for all columns
- Always set `nullable=True` for optional fields
- Use `default` and `server_default` for default values
- Define relationships with proper `back_populates`
- Use `TYPE_CHECKING` block for forward references (see "Forward References with TYPE_CHECKING" below)
- Include `__table_args__ = {"extend_existing": True}` in all models

### Creating New Models with Alembic

**Migration Naming Convention**: `YYYY_MM_DD_HHMM-{hash}_{snake_case_description}.py`

#### One-to-One Relationships

**Pattern**: Foreign key column + `unique=True` constraint

```python
# src/core/models/scoreboard.py
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .match import MatchDB


class ScoreboardDB(Base):
    __tablename__ = "scoreboard"
    __table_args__ = {"extend_existing": True}

    match_id: Mapped[int] = mapped_column(
        ForeignKey("match.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,  # Makes this one-to-one
    )

    matches: Mapped["MatchDB"] = relationship(
        "MatchDB",
        back_populates="match_scoreboard",
    )
```

**Alembic Migration**:
```python
def upgrade() -> None:
    op.add_column("scoreboard", sa.Column("match_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        None, "scoreboard", "match", ["match_id"], ["id"], ondelete="CASCADE"
    )
    op.create_unique_constraint(None, "scoreboard", ["match_id"])

def downgrade() -> None:
    op.drop_constraint(None, "scoreboard", type_="foreignkey")
    op.drop_constraint(None, "scoreboard", type_="unique")
    op.drop_column("scoreboard", "match_id")
```

#### One-to-Many Relationships

**Pattern**: Parent-child with `cascade="all, delete-orphan"` and `passive_deletes=True`

```python
# src/core/models/match.py
class MatchDB(Base):
    __tablename__ = "match"
    __table_args__ = {"extend_existing": True}

    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournament.id", ondelete="CASCADE"),
        nullable=True,
    )

    match_events: Mapped[list["FootballEventDB"]] = relationship(
        "FootballEventDB",
        cascade="all, delete-orphan",
        back_populates="matches",
        passive_deletes=True,
    )
```

**Alembic Migration**:
```python
def upgrade() -> None:
    op.create_table(
        "match",
        sa.Column("tournament_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["tournament_id"],
            ["tournament.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

def downgrade() -> None:
    op.drop_table("match")
```

#### Many-to-Many Relationships

**Pattern**: Association table with composite primary key

```python
# src/core/models/user.py
if TYPE_CHECKING:
    from .role import RoleDB


class UserDB(Base):
    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}

    roles: Mapped[list["RoleDB"]] = relationship(
        "RoleDB",
        secondary="user_role",
        back_populates="users",
    )
```

**Association Table**:
```python
# src/core/models/user_role.py
from sqlalchemy import Column, ForeignKey, Integer, Table

user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
)
```

**Alembic Migration**:
```python
def upgrade() -> None:
    op.create_table(
        "user_role",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

def downgrade() -> None:
    op.drop_table("user_role")
```

**Many-to-Many with Extra Columns** (e.g., player_team_tournament):
```python
# Association table with extra data
op.create_table(
    "player_team_tournament",
    sa.Column("player_id", sa.Integer(), nullable=True),
    sa.Column("team_id", sa.Integer(), nullable=True),
    sa.Column("tournament_id", sa.Integer(), nullable=True),
    sa.Column("player_number", sa.String(length=10), server_default="0", nullable=True),
    sa.Column("player_position", sa.String(length=20), server_default="", nullable=True),
    sa.Column("id", sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(["player_id"], ["player.id"], ondelete="CASCADE"),
    sa.ForeignKeyConstraint(["team_id"], ["team.id"], ondelete="SET NULL"),
    sa.ForeignKeyConstraint(["tournament_id"], ["tournament.id"], ondelete="SET NULL"),
    sa.PrimaryKeyConstraint("id"),
)
```

#### Self-Referencing Relationships

**Pattern**: Multiple foreign keys to same table with explicit `foreign_keys` parameter

```python
# src/core/models/match.py
class MatchDB(Base):
    __tablename__ = "match"

    team_a_id: Mapped[int] = mapped_column(
        ForeignKey("team.id", ondelete="CASCADE"),
        nullable=False,
    )

    team_b_id: Mapped[int] = mapped_column(
        ForeignKey("team.id", ondelete="CASCADE"),
        nullable=False,
    )

    team_a: Mapped["TeamDB"] = relationship(
        "TeamDB",
        foreign_keys=[team_a_id],
        back_populates="matches_as_team_a",
        viewonly=True,
    )

    team_b: Mapped["TeamDB"] = relationship(
        "TeamDB",
        foreign_keys=[team_b_id],
        back_populates="matches_as_team_b",
        viewonly=True,
    )
```

**Custom Join Condition** (OR condition):
```python
# src/core/models/team.py
matches: Mapped[list["MatchDB"]] = relationship(
    "MatchDB",
    primaryjoin="or_(TeamDB.id==MatchDB.team_a_id, TeamDB.id==MatchDB.team_b_id)",
    back_populates="teams",
    uselist=True,
)
```

#### Relationship Naming Conventions

| Relationship Type | Child Side (FK) | Parent Side (Collection) |
|-----------------|----------------|-------------------------|
| One-to-many | `sport_id: Mapped[int]` | `tournaments: Mapped[list["TournamentDB"]]` |
| Many-to-one | `sport: Mapped["SportDB"]` | - |
| One-to-one | `match_id: Mapped[int]` with `unique=True` | `match_scoreboard: Mapped["ScoreboardDB"]` |
| Many-to-many | Uses `secondary="association_table"` | Uses `secondary="association_table"` |

#### Cascade Options

- **`cascade="all, delete-orphan"`**: Delete children when parent is deleted (standard parent-child)
- **`cascade="save-update, merge"`**: Only save/update/merge, don't delete children (many-to-many)
- **`passive_deletes=True`**: Use database-level CASCADE (requires FK `ondelete="CASCADE"`)

#### Foreign Key ON DELETE Options

- **`ondelete="CASCADE"`**: Delete dependent records (most common)
- **`ondelete="SET NULL"`**: Set FK to NULL when parent deleted (optional relationships)
- **No `ondelete`**: Restrict deletion if dependent records exist

#### Index Creation on Relationship Columns

```python
# Composite index on foreign keys
op.create_index(
    "ix_match_tournament_id_team_a_id_team_b_id",
    "match",
    ["tournament_id", "team_a_id", "team_b_id"]
)

# Single column index
op.create_index(
    "ix_football_event_match_id",
    "football_event",
    ["match_id"]
)
```

**Naming convention**: `ix_{table_name}_{column_names_underscored}`

### Forward References with TYPE_CHECKING

**Purpose**: Break circular import dependencies while maintaining type safety for static analysis

```python
# src/core/models/user.py
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

# TYPE_CHECKING block: imports only execute during type checking, not runtime
if TYPE_CHECKING:
    from .person import PersonDB
    from .role import RoleDB


class UserDB(Base):
    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}

    person_id: Mapped[int] = mapped_column(
        ForeignKey("person.id", ondelete="CASCADE"),
        nullable=True,
    )

    # String annotations allow SQLAlchemy to defer resolution
    person: Mapped["PersonDB"] = relationship(
        "PersonDB",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    roles: Mapped[list["RoleDB"]] = relationship(
        "RoleDB",
        secondary="user_role",
        back_populates="users",
    )
```

#### Import Structure

```python
# 1. Standard library imports
from typing import TYPE_CHECKING

# 2. Third-party imports
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

# 3. Local imports
from src.core.models import Base

# 4. TYPE_CHECKING block (after imports, before class)
if TYPE_CHECKING:
    from .person import PersonDB
    from .role import RoleDB

# 5. Class definition
class UserDB(Base):
    ...
```

#### Import Format Rules

- **Models in same directory**: Use relative imports with single dot (`from .person import PersonDB`)
- **Models from mixins directory**: Use double dots (`..`) to go up one level (`from ..season import SeasonDB`)
- **Never use absolute imports** in TYPE_CHECKING block for models in same package
- **No aliases**: Import full model name (not `from .person import PersonDB as Person`)

#### Empty TYPE_CHECKING Blocks

If no relationships are defined (e.g., join tables with only FKs):

```python
# src/core/models/team_tournament.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # No relationships, so no imports needed


class TeamTournamentDB(Base):
    # ... only foreign keys, no relationship() definitions
```

#### Relationship Type Hints

```python
# Single relationship (many-to-one or one-to-one)
person: Mapped["PersonDB"] = relationship("PersonDB", ...)

# List relationship (one-to-many)
tournaments: Mapped[list["TournamentDB"]] = relationship("TournamentDB", ...)
```

#### TYPE_CHECKING in Mixins

```python
# src/core/models/mixins/season_sport_mixin.py
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

if TYPE_CHECKING:
    from ..season import SeasonDB  # Double dots to go up from mixins/
    from ..sport import SportDB


class SeasonSportRelationMixin:
    @declared_attr
    def season_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("season.id", ondelete=cls._ondelete))

    @declared_attr
    def season(cls) -> Mapped["SeasonDB"]:
        return relationship("SeasonDB", back_populates=cls._season_back_populates)
```

#### Why This Works

1. **Runtime (TYPE_CHECKING=False)**: Imports inside block are skipped, no circular dependencies
2. **Type Checking (TYPE_CHECKING=True)**: Imports execute, type checkers see actual classes
3. **SQLAlchemy**: String annotations (`"PersonDB"`) work with `relationship()` regardless of actual class

#### Common Pitfalls to Avoid

- **Mistake 1**: Direct imports outside TYPE_CHECKING block
  ```python
  # BAD - causes circular import
  from .person import PersonDB
  person: Mapped[PersonDB] = relationship(PersonDB, ...)
  ```

- **Mistake 2**: Using TYPE_CHECKING but not using string annotations
  ```python
  # BAD - defeats purpose
  if TYPE_CHECKING:
      from .person import PersonDB
  person: Mapped[PersonDB] = relationship(PersonDB, ...)  # Fails at runtime
  ```

- **Mistake 3**: Not importing types in TYPE_CHECKING block
  ```python
  # BAD - no type safety, no autocomplete
  if TYPE_CHECKING:
      pass
  person: Mapped["PersonDB"] = relationship("PersonDB", ...)  # Type checker can't verify
  ```

## Error Handling

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
    async with self.db.get_session_maker()() as session:
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

**For view endpoints (FastAPI routers):** Use `@handle_view_exceptions` decorator:

```python
from src.core.models import handle_view_exceptions

# Upload endpoints with file operations
@router.post("/upload_logo", response_model=UploadTeamLogoResponse)
@handle_view_exceptions(
    error_message="Error uploading team logo",
    status_code=500,
)
async def upload_team_logo_endpoint(file: UploadFile = File(...)):
    file_location = await file_service.save_upload_image(file, sub_folder="teams/logos")
    return {"logoUrl": file_location}

# Complex endpoints with service calls
@router.get("/id/{team_id}/matches/")
@handle_view_exceptions(
    error_message="Internal server error fetching matches for team",
    status_code=500,
)
async def get_matches_by_team_endpoint(team_id: int):
    return await self.service.get_matches_by_team_id(team_id)
```

The `@handle_view_exceptions` decorator:
- Catches `HTTPException` and re-raises as-is to preserve status codes and messages
- Catches other exceptions, logs them with error level, and converts to `HTTPException`
- Supports custom error messages and status codes
- Automatically extracts logger from `self.logger` for consistent logging

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
       raise HTTPException(status_code=500, detail="Database error") from ex
   except ValidationError as ex:
       # Validation errors
       self.logger.warning(f"Validation error: {ex}", exc_info=True)
       raise HTTPException(status_code=400, detail=str(ex)) from ex
   except (ValueError, KeyError, TypeError) as ex:
       # Data errors
       self.logger.warning(f"Data error: {ex}", exc_info=True)
       raise HTTPException(status_code=400, detail="Invalid data") from ex
   except NotFoundError as ex:
       # Not found
       self.logger.info(f"Not found: {ex}", exc_info=True)
       raise HTTPException(status_code=404, detail=str(ex)) from ex
   except BusinessLogicError as ex:
       # Business logic errors
       self.logger.error(f"Business logic error: {ex}", exc_info=True)
       raise HTTPException(status_code=422, detail=str(ex)) from ex
   except Exception as ex:
       # Only for truly unexpected errors - should rarely trigger
       self.logger.critical(f"Unexpected error: {ex}", exc_info=True)
       raise HTTPException(status_code=500, detail="Internal server error") from ex
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

## Logging

- Call `setup_logging()` at module level in services and routers
- Initialize logger with short, descriptive name: `get_logger("TeamServiceDB", self)`
- Use appropriate log levels:
  - `debug`: Detailed operation tracking
  - `info`: Significant operations (creates, updates)
  - `warning`: Expected but noteworthy situations
  - `error`: Unexpected errors with exceptions

### Request ID Middleware

The application includes automatic request ID tracking via `RequestIDMiddleware` in `src/main.py`:
- Each request gets a unique ID (either from `X-Request-ID` header or auto-generated UUID4)
- Request ID is available in `request.state.request_id` throughout the request lifecycle
- Request ID is included in response headers (`X-Request-ID`)
- Request ID is included in all error responses for traceability

### Logging Middleware

Automatic request/response logging via `LoggingMiddleware` in `src/main.py`:
- Logs request start with method, path, and request_id
- Logs request completion with status code, duration (in ms), and request_id
- Logs request failures with error type and full exception info
- Enables correlation of logs across services using request_id

### Using Request IDs in Custom Code

```python
from fastapi import Request

async def my_endpoint(request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(f"Processing with request_id={request_id}")
```

## Testing

- Use `@pytest.mark.asyncio` for async test classes
- Use fixtures from `tests/fixtures.py` for common setup
- Use factory classes from `tests/factories.py` for test data
- Write descriptive docstrings for test methods
- Use helper functions from `tests/testhelpers.py` for assertions
- Test both success and error paths
- **Never suppress exceptions in fixtures**: Let exceptions propagate to expose fixture failures immediately. Exception masking leads to confusing downstream test failures with unclear error messages

### Testing Enhancements

The project includes several enhanced testing approaches:

**1. Test Factories with SubFactory** (`tests/factories.py`):

- Basic factories: `SportFactoryAny`, `SeasonFactoryAny`, `TournamentFactory`, etc.
- Enhanced factories with relations: `TournamentFactoryWithRelations`, `TeamFactoryWithRelations`, etc.
- Use SubFactory for automatic creation of related entities
- Example: `TournamentFactoryWithRelations.build()` creates sport, season, and tournament

**2. Property-Based Testing** (`tests/test_property_based.py`):

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
- Transaction rollback per test: Fast cleanup without table drops
- No Alembic migrations: Direct table creation with file-based lock coordination
- Parallel test execution with pytest-xdist: `-n 4` uses 4 workers across 4 databases (test_db, test_db2, test_db3, test_db4)
- PostgreSQL performance tuning in docker-compose.test-db-only.yml:
  - fsync=off, synchronous_commit=off, full_page_writes=off
  - wal_level=minimal, max_wal_senders=0
  - autovacuum=off, track_functions=none, track_counts=off
  - tmpfs for PostgreSQL data (in-memory storage)
  - Creates test_db, test_db2, test_db3, test_db4 databases on startup
- Worker-specific lock files (`/tmp/test_db_tables_setup_{db_name}.lock`) coordinate table creation across parallel workers
- Worker distribution: gw0 → test_db; gw1 → test_db2; gw2 → test_db3; gw3 → test_db4
- Database connections properly closed after each test to prevent ResourceWarnings

**Important:** Test fixtures use `test_mode=True` in Database class, which automatically replaces `commit()` with `flush()` in CRUDMixin to avoid deadlocks during parallel execution. The outer test fixture handles rollback automatically:

```python
# Test fixtures in tests/conftest.py
database = Database(test_db_url, echo=False, test_mode=True)
```

When writing direct session code in test fixtures, always use `test_db.get_session_maker()()`:

```python
async with test_db.get_session_maker()() as db_session:
    role = RoleDB(name="test_role", description="Test role")
    db_session.add(role)
    await db_session.flush()  # Use flush() instead of commit()
```

**Test Results:**

All 1465 tests pass reliably in ~160s with 4 parallel workers (`-n 4`) across 4 databases. Worker-specific lock files ensure tables and indexes are created safely across workers, and using `flush()` in test fixtures eliminates deadlock issues.

**Known Warnings:**

None. Previously had deprecation warnings from `passlib` library (using deprecated `crypt` module). These were resolved by removing `passlib` and using `bcrypt` directly (v4.3.0) for password hashing.

## Database Operations

- Always use async context managers: `async with self.db.get_session_maker()() as session:`
- Use SQLAlchemy 2.0 select API: `select(Model).where(Model.field == value)`
- Use `session.execute(stmt)` and `results.scalars().all()` for queries
- Never commit manually in service methods - let BaseServiceDB handle it
- Use relationships defined in models rather than manual joins
- **Use eager loading** (`selectinload()`) to prevent N+1 query problems (see "Fetching Complex Relationships in Services" below)
- **Add `order_by` to relationships** for predictable query results, especially important for parallel test execution

### File Structure Per Domain

Each domain module must contain:

- `schemas.py`: Pydantic models for API contracts
- `db_services.py`: Service class inheriting from `BaseServiceDB`
- `views.py`: Router class inheriting from `BaseRouter`
- `__init__.py`: Exports router as `api_<domain>_router`

### Fetching Complex Relationships in Services

#### Loading Strategy Recommendations

- **Prefer `selectinload()`** over `joinedload()` for most relationship loading (better for many-to-many)
- **Chain `selectinload()`** for 2+ level deep nested relationships
- **Use base mixin methods** (`get_related_item_level_one_by_id()`, `get_nested_related_item_by_id()`) when possible for consistency
- **Add indexes** on frequently queried foreign key combinations for performance

#### Level 1 Relationship Loading

Use base utility methods from `RelationshipMixin` with `selectinload()` for eager loading.

**Pattern**: `get_related_item_level_one_by_id(item_id, relationship_name)`

```python
# src/tournaments/db_services.py
async def get_teams_by_tournament(
    self,
    tournament_id: int,
) -> list[TeamDB]:
    self.logger.debug(f"Get teams by {ITEM} id:{tournament_id}")
    return await self.get_related_item_level_one_by_id(
        tournament_id,
        "teams",
    )
```

#### Nested Relationship Loading (2+ Levels Deep)

Use chained `selectinload()` for eager loading multiple relationship levels in a single query.

```python
# src/matches/db_services.py
async def get_player_by_match_full_data(self, match_id: int) -> list[dict]:
    from src.core.models.player import PlayerDB
    from src.core.models.player_team_tournament import PlayerTeamTournamentDB

    async with self.db.get_session_maker()() as session:
        stmt = (
            select(PlayerMatchDB)
            .where(PlayerMatchDB.match_id == match_id)
            .options(
                # 3-level deep loading: PlayerMatch -> PlayerTeamTournament -> Player -> Person
                selectinload(PlayerMatchDB.player_team_tournament)
                .selectinload(PlayerTeamTournamentDB.player)
                .selectinload(PlayerDB.person),
                # Parallel level 2 relationships
                selectinload(PlayerMatchDB.match_position),
                selectinload(PlayerMatchDB.team),
            )
        )

        results = await session.execute(stmt)
        players = results.scalars().all()

        # Build complex data structure
        players_with_data = []
        for player in players:
            players_with_data.append(
                {
                    "id": player.id,
                    "player_id": (
                        player.player_team_tournament.player_id
                        if player.player_team_tournament
                        else None
                    ),
                    "player": (
                        player.player_team_tournament.player
                        if player.player_team_tournament
                        else None
                    ),
                    "team": player.team,
                    "position": (
                        {
                            **player.match_position.__dict__,
                            "category": player.match_position.category,
                        }
                        if player.match_position
                        else None
                    ),
                    "player_team_tournament": player.player_team_tournament,
                    "person": (
                        player.player_team_tournament.player.person
                        if player.player_team_tournament
                        and player.player_team_tournament.player
                        else None
                    ),
                    "is_starting": player.is_starting,
                    "starting_type": player.starting_type,
                }
            )

        return players_with_data
```

#### Many-to-Many Relationship Loading

Use direct `select()` queries with where clauses for filtering junction tables.

```python
# src/teams/db_services.py
async def get_players_by_team_id_tournament_id(
    self,
    team_id: int,
    tournament_id: int,
) -> list[PlayerTeamTournamentDB]:
    self.logger.debug(f"Get players by {ITEM} id:{team_id} and tournament id:{tournament_id}")
    async with self.db.get_session_maker()() as session:
        stmt = (
            select(PlayerTeamTournamentDB)
            .where(PlayerTeamTournamentDB.team_id == team_id)
            .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
        )

        results = await session.execute(stmt)
        players = results.scalars().all()
        return players
```

**Join for many-to-many**:
```python
async def get_related_teams(self, tournament_id: int) -> list[TeamDB]:
    self.logger.debug(f"Get {ITEM} related teams for tournament_id:{tournament_id}")
    async with self.db.get_session_maker()() as session:
        result = await session.execute(
            select(TeamDB)
            .join(TeamTournamentDB)
            .where(TeamTournamentDB.tournament_id == tournament_id)
        )
        teams = result.scalars().all()
        return teams
```

#### Custom Relationship Queries with Subqueries

Use subqueries to exclude certain records.

```python
# src/matches/db_services.py
async def _get_available_players(
    self, session, team_id: int, tournament_id: int, match_id: int
) -> list[dict]:
    """Get players available for match (not already in match)."""
    from src.core.models.player import PlayerDB

    # Subquery to find players already in match
    subquery = (
        select(PlayerMatchDB.player_team_tournament_id)
        .where(PlayerMatchDB.match_id == match_id)
        .where(PlayerMatchDB.team_id == team_id)
    )

    # Get players NOT in the subquery (available players)
    stmt = (
        select(PlayerTeamTournamentDB)
        .where(PlayerTeamTournamentDB.team_id == team_id)
        .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
        .where(~PlayerTeamTournamentDB.id.in_(subquery))  # NOT IN subquery
        .options(
            selectinload(PlayerTeamTournamentDB.player).selectinload(PlayerDB.person),
            selectinload(PlayerTeamTournamentDB.position),
            selectinload(PlayerTeamTournamentDB.team),
        )
    )

    results = await session.execute(stmt)
    available_players = results.scalars().all()

    return [
        {
            "id": pt.id,
            "player_id": pt.player_id,
            "player_team_tournament": pt,
            "person": pt.player.person if pt.player else None,
            "position": pt.position,
            "team": pt.team,
        }
        for pt in available_players
    ]
```

#### Joins with Nullable Foreign Keys

**Use `outerjoin()` instead of `join()` when the foreign key is nullable** to include records where the related field is `NULL`.

**Problem**: Inner joins filter out records with `NULL` foreign keys.

**Example - PlayerTeamTournament with optional team assignment**:

```python
# WRONG - Filters out players with team_id: NULL
base_query = (
    select(PlayerTeamTournamentDB)
    .join(PlayerDB, PlayerTeamTournamentDB.player_id == PlayerDB.id)
    .join(PersonDB, PlayerDB.person_id == PersonDB.id)
    .join(TeamDB, PlayerTeamTournamentDB.team_id == TeamDB.id)  # INNER JOIN
    .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
)

# CORRECT - Includes players with team_id: NULL
base_query = (
    select(PlayerTeamTournamentDB)
    .join(PlayerDB, PlayerTeamTournamentDB.player_id == PlayerDB.id)
    .join(PersonDB, PlayerDB.person_id == PersonDB.id)
    .outerjoin(TeamDB, PlayerTeamTournamentDB.team_id == TeamDB.id)  # OUTER JOIN
    .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
)
```

**Rules**:
- Use `join()` for required relationships (non-nullable FK, `ondelete="CASCADE"`)
- Use `outerjoin()` for optional relationships (nullable FK, `ondelete="SET NULL"` or `ondelete="RESTRICT"`)
- Check model definition: `ForeignKey("table.id", ondelete="...")` with `nullable=True` → use `outerjoin()`

**Example - Tournament players paginated with optional team**:

```python
# src/player_team_tournament/db_services.py
async def _build_base_query_with_search(
    self,
    tournament_id: int,
    search_query: str | None = None,
    team_title: str | None = None,
):
    search_fields = [
        (PersonDB, "first_name"),
        (PersonDB, "second_name"),
    ]

    if search_query or team_title:
        base_query = (
            select(PlayerTeamTournamentDB)
            .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
            .join(PlayerDB, PlayerTeamTournamentDB.player_id == PlayerDB.id)
            .join(PersonDB, PlayerDB.person_id == PersonDB.id)
            .outerjoin(TeamDB, PlayerTeamTournamentDB.team_id == TeamDB.id)  # team_id is nullable
            .outerjoin(PositionDB, PlayerTeamTournamentDB.position_id == PositionDB.id)  # position_id is nullable
            .options(
                selectinload(PlayerTeamTournamentDB.player).selectinload(PlayerDB.person),
                selectinload(PlayerTeamTournamentDB.team),
                selectinload(PlayerTeamTournamentDB.position),
            )
        )
        ...
```

**Testing**: Always test both cases - records with the FK set and records with `NULL` values.

#### Nested Related Items Using Service Registry

Use `get_nested_related_item_by_id()` to traverse 2-level relationships using a different service.

```python
# src/tournaments/db_services.py
async def get_sponsors_of_tournament_sponsor_line(self, tournament_id: int) -> list[SponsorDB]:
    sponsor_line_service = self.service_registry.get("sponsor_line")
    self.logger.debug(f"Get sponsors of tournament sponsor line {ITEM} id:{tournament_id}")
    # Tournament -> SponsorLine -> Sponsors
    return await self.get_nested_related_item_by_id(
        tournament_id,
        sponsor_line_service,
        "sponsor_line",
        "sponsors",
    )
```

```python
# src/player_match/db_services.py
async def get_player_in_sport(self, player_id: int) -> PlayerDB | None:
    player_team_tournament_service = self.service_registry.get("player_team_tournament")
    self.logger.debug(f"Get player in sport by player_id:{player_id}")
    # PlayerMatch -> PlayerTeamTournament -> Player
    return await self.get_nested_related_item_by_id(
        player_id,
        player_team_tournament_service,
        "player_team_tournament",
        "player",
    )
```

#### Complex Multi-Query Assembly

Combine multiple queries to build a complete context.

```python
# src/matches/db_services.py
async def get_match_full_context(self, match_id: int) -> dict | None:
    """Get match with all initialization data: teams, sport, positions, players."""
    from src.core.models.player import PlayerDB

    async with self.db.get_session_maker()() as session:
        # Query 1: Match with teams and tournament
        stmt = (
            select(MatchDB)
            .where(MatchDB.id == match_id)
            .options(
                selectinload(MatchDB.team_a),
                selectinload(MatchDB.team_b),
                selectinload(MatchDB.tournaments),
            )
        )

        result = await session.execute(stmt)
        match = result.scalar_one_or_none()

        if not match:
            return None

        tournament = match.tournaments if match.tournaments else None

        # Query 2: Sport with positions
        if tournament:
            stmt_sport = (
                select(SportDB)
                .where(SportDB.id == tournament.sport_id)
                .options(selectinload(SportDB.positions))
            )
            result_sport = await session.execute(stmt_sport)
            sport = result_sport.scalar_one_or_none()
        else:
            sport = None

        # Query 3: Players with nested relationships
        stmt_players = (
            select(PlayerMatchDB)
            .where(PlayerMatchDB.match_id == match_id)
            .options(
                selectinload(PlayerMatchDB.player_team_tournament)
                .selectinload(PlayerTeamTournamentDB.player)
                .selectinload(PlayerDB.person),
                selectinload(PlayerMatchDB.match_position),
                selectinload(PlayerMatchDB.team),
            )
        )
        result_players = await session.execute(stmt_players)
        player_matches = result_players.scalars().all()

        # Query 4 & 5: Available players for home/away teams
        home_available = await self._get_available_players(
            session, match.team_a_id, match.tournament_id, match_id
        )
        away_available = await self._get_available_players(
            session, match.team_b_id, match.tournament_id, match_id
        )

        # Build final composite structure
        return {
            "match": match.__dict__,
            "teams": {
                "home": match.team_a.__dict__ if match.team_a else None,
                "away": match.team_b.__dict__ if match.team_b else None,
            },
            "sport": {
                **(sport.__dict__ if sport else {}),
                "positions": [pos.__dict__ for pos in sport.positions] if sport else [],
            },
            "tournament": tournament.__dict__ if tournament else None,
            "players": {
                "home_roster": home_roster,
                "away_roster": away_roster,
                "available_home": home_available,
                "available_away": away_available,
            },
        }
```

#### Pagination with Relationship Loading

Use `get_related_item_level_one_by_id()` with pagination parameters.

```python
# src/tournaments/db_services.py
async def get_matches_by_tournament_with_pagination(
    self,
    tournament_id: int,
    skip: int = 0,
    limit: int = 20,
    order_exp: str = "id",
    order_exp_two: str = "id",
) -> list[MatchDB]:
    self.logger.debug(
        f"Get matches by {ITEM} id:{tournament_id} with pagination: skip={skip}, limit={limit}"
    )
    return await self.get_related_item_level_one_by_id(
        tournament_id,
        "matches",
        skip=skip,
        limit=limit,
        order_by=order_exp,
        order_by_two=order_exp_two,
    )
```

#### Base Utility Methods from RelationshipMixin

Key utility methods provided by base class:

| Method | Purpose |
|--------|---------|
| `get_related_item_level_one_by_id(id, relation)` | Fetch level 1 relationships with `selectinload()` |
| `get_nested_related_item_by_id(id, service, rel1, rel2)` | Fetch 2-level nested relationships |
| `create_m2m_relation(...)` | Create many-to-many relationships |
| `find_relation(...)` | Check if relation exists in junction table |
| `get_related_items(...)` | Fetch related items with optional property loading |
| `get_related_items_by_two(...)` | Fetch 2-level relationships using `joinedload()` |
| `first_or_none(result)` | Normalize relationship query results (return first item if list, or None) |

#### Key Patterns Summary

1. **`selectinload()`** - Primary loading strategy for eager loading relationships
2. **Chained `selectinload()`** - For 2+ level deep relationships (e.g., `.selectinload(A).selectinload(B)`)
3. **Base mixin methods** - Reusable patterns for common relationship queries
4. **Direct `select()` with `where()`** - For many-to-many junction table queries
5. **Subqueries with `NOT IN`** - For exclusion queries (e.g., "available players")
6. **Service registry** - For cross-service nested relationships
7. **Multi-query assembly** - Building complex composite data structures

### Combined Pydantic Schemas

**See [COMBINED_SCHEMAS.md](COMBINED_SCHEMAS.md)** for comprehensive guide on:

- **Available combined schemas**: Full list of schemas with nested relationships (`MatchWithDetailsSchema`, `TeamWithDetailsSchema`, etc.)
- **How to use them**: API endpoints, response examples, frontend integration patterns
- **Creating new complex schemas**: Step-by-step guide with eager loading strategies
- **Performance considerations**: Choosing between `joinedload` vs `selectinload`, avoiding N+1 queries
- **Best practices**: Circular import handling, `from_attributes=True`, pagination wrappers, testing patterns

**Quick Reference:**

| Schema | Endpoint | Use Case |
|--------|----------|-----------|
| `MatchWithDetailsSchema` | `GET /api/matches/{id}/with-details/` | Full match display with teams, tournament |
| `TeamWithDetailsSchema` | `GET /api/teams/{id}/with-details/` | Team page with sport, sponsors |
| `TournamentWithDetailsSchema` | `GET /api/tournaments/{id}/with-details/` | Tournament page with all teams |
| `PlayerTeamTournamentWithDetailsAndPhotosSchema` | `GET /api/players_team_tournament/tournament/{tournament_id}/players/paginated/details-with-photos` | Tournament player list with photos for avatars |

**Key Pattern:**

```python
# Service method with eager loading
async def get_match_with_details(self, match_id: int) -> MatchDB | None:
    async with self.db.get_session_maker()() as session:
        stmt = (
            select(MatchDB)
            .where(MatchDB.id == match_id)
            .options(
                joinedload(MatchDB.team_a),  # Single: use joinedload
                joinedload(MatchDB.team_b),
                joinedload(MatchDB.tournaments),  # Single: use joinedload
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

# API endpoint returns combined schema
@router.get("/id/{match_id}/with-details/", response_model=MatchWithDetailsSchema)
async def get_match_with_details_endpoint(match_id: int):
    match = await self.service.get_match_with_details(match_id)
    return MatchWithDetailsSchema.model_validate(match)
```

## Search Implementation

When adding search functionality to a domain:

### 1. Schema Updates

Add pagination metadata and paginated response schemas:

```python
# src/{domain}/schemas.py
class PaginationMetadata(BaseModel):
    page: int
    items_per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class Paginated{Entity}Response(BaseModel):
    data: list[{Entity}Schema]
    metadata: PaginationMetadata
```

### 2. Service Layer Implementation

Implement `search_<entity>s_with_pagination()` method:

```python
# src/{domain}/db_services.py
from math import ceil
from sqlalchemy import select, func

@handle_service_exceptions(
    item_name=ITEM,
    operation="searching {entity}s with pagination",
    return_value_on_not_found=None,
)
async def search_{entity}s_with_pagination(
    self,
    search_query: str | None = None,
    skip: int = 0,
    limit: int = 20,
    order_by: str = "{default_field}",
    order_by_two: str = "id",
    ascending: bool = True,
) -> Paginated{Entity}Response:
    self.logger.debug(
        f"Search {ITEM}: query={search_query}, skip={skip}, limit={limit}, "
        f"order_by={order_by}, order_by_two={order_by_two}"
    )

    async with self.db.get_session_maker()() as session:
        base_query = select({Model}DB)

        # Search pattern matching with ICU collation for international text
        if search_query:
            search_pattern = f"%{search_query}%"
            base_query = base_query.where(
                ({Model}DB.field1.ilike(search_pattern).collate("en-US-x-icu"))
                | ({Model}DB.field2.ilike(search_pattern).collate("en-US-x-icu"))
            )

        # Get total count
        count_stmt = select(func.count()).select_from(base_query.subquery())
        count_result = await session.execute(count_stmt)
        total_items = count_result.scalar() or 0

        total_pages = ceil(total_items / limit) if limit > 0 else 0

        # Order by columns with fallbacks
        try:
            order_column = getattr({Model}DB, order_by, {Model}DB.{default_field})
        except AttributeError:
            self.logger.warning(f"Order column {order_by} not found, defaulting to {default_field}")
            order_column = {Model}DB.{default_field}

        try:
            order_column_two = getattr({Model}DB, order_by_two, {Model}DB.id)
        except AttributeError:
            self.logger.warning(f"Order column {order_by_two} not found, defaulting to id")
            order_column_two = {Model}DB.id

        order_expr = order_column.asc() if ascending else order_column.desc()
        order_expr_two = order_column_two.asc() if ascending else order_column_two.desc()

        # Apply pagination and ordering
        data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
        result = await session.execute(data_query)
        {entity}s = result.scalars().all()

        return Paginated{Entity}Response(
            data=[{Entity}Schema.model_validate(e) for e in {entity}s],
            metadata=PaginationMetadata(
                page=(skip // limit) + 1,
                items_per_page=limit,
                total_items=total_items,
                total_pages=total_pages,
                has_next=(skip + limit) < total_items,
                has_previous=skip > 0,
            ),
        )
```

### 3. Router Layer Updates

Add `search` query parameter to paginated endpoint:

```python
# src/{domain}/views.py
@router.get(
    "/paginated",
    response_model=Paginated{Entity}Response,
)
async def get_all_{entity}s_paginated_endpoint(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    items_per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    order_by: str = Query("{default_field}", description="First sort column"),
    order_by_two: str = Query("id", description="Second sort column"),
    ascending: bool = Query(True, description="Sort order (true=asc, false=desc)"),
    search: str | None = Query(None, description="Search query for text search"),
):
    self.logger.debug(
        f"Get all {entity}s paginated: page={page}, items_per_page={items_per_page}, "
        f"order_by={order_by}, order_by_two={order_by_two}, ascending={ascending}, search={search}"
    )
    skip = (page - 1) * items_per_page
    response = await self.service.search_{entity}s_with_pagination(
        search_query=search,
        skip=skip,
        limit=items_per_page,
        order_by=order_by,
        order_by_two=order_by_two,
        ascending=ascending,
    )
    return response
```

### Key Implementation Details

1. **Search Pattern Matching**:
   - Uses `ilike()` for case-insensitive matching
   - ICU collation (`en-US-x-icu`) for proper international text handling
   - Pattern `%query%` matches anywhere in the field
   - Searches multiple fields with OR (`|`) operator

2. **Pagination Metadata**:
   - `page`: Current page number (1-based)
   - `items_per_page`: Number of items per page
   - `total_items`: Total number of matching results
   - `total_pages`: Total number of pages (ceil(total_items / items_per_page))
   - `has_next`: Whether there is a next page
   - `has_previous`: Whether there is a previous page

 3. **Ordering**:
    - Dual column sorting for consistent pagination
    - Graceful fallback to default columns if invalid column names provided
    - Configurable ascending/descending order

  4. **Empty Search Query**:
     - `search=None` returns all records with pagination
     - Consistent with existing `get_all_with_pagination()` behavior

   5. **Error Handling**:
     - Decorator with `return_value_on_not_found=None` for graceful handling
     - Returns empty list and zero metadata when no results found

### Ordering by Joined Table Fields

When implementing search endpoints with joins, ordering by fields from joined tables (e.g., `PersonDB.first_name`, `TeamDB.title`) requires a custom approach since the default `_build_order_expressions` method only looks at the primary model.

#### Problem

The `_build_order_with_fallback` method in `SearchPaginationMixin` uses `getattr(model, column_name)` which only finds columns on the passed model:

```python
# In SearchPaginationMixin
async def _get_column_with_fallback(self, model, column_name: str, default_column):
    try:
        return getattr(model, column_name)  # ❌ Fails for joined table columns
    except AttributeError:
        self.logger.warning(f"Order column {column_name} not found...")
        return default_column  # ❌ Falls back to default even for valid joined fields
```

When querying `PlayerTeamTournamentDB` with joins to `PersonDB`, ordering by `second_name` (which exists on `PersonDB`) would fail and fall back to `player_number`.

#### Solution

Use the `_build_order_expressions_with_mapping` method from `SearchPaginationMixin` which accepts a field mapping dictionary:

```python
async def _build_order_expressions_with_joins(
    self,
    order_by: str,
    order_by_two: str | None,
    ascending: bool,
) -> tuple:
    """Build order expressions with support for joined table fields."""
    field_mapping = {
        "id": PlayerTeamTournamentDB.id,
        "player_number": PlayerTeamTournamentDB.player_number,
        "player_team_tournament_eesl_id": PlayerTeamTournamentDB.player_team_tournament_eesl_id,
        "first_name": PersonDB.first_name,
        "second_name": PersonDB.second_name,
        "team_title": TeamDB.title,
        "position_title": PositionDB.title,
    }

    return await self._build_order_expressions_with_mapping(
        field_mapping=field_mapping,
        order_by=order_by,
        order_by_two=order_by_two,
        ascending=ascending,
        default_column=PlayerTeamTournamentDB.player_number,
        default_column_two=PlayerTeamTournamentDB.id,
    )
```

Then use it in your search method instead of `_build_order_expressions`:

```python
async def search_tournament_players_with_pagination_details_and_photos(...):
    base_query = await self._build_base_query_with_search(...)

    order_expr, order_expr_two = await self._build_order_expressions_with_joins(
        order_by,
        order_by_two,
        ascending,
    )

    data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
```

The `_build_order_expressions_with_mapping` method in `SearchPaginationMixin` provides the generalized logic for handling field mappings and defaults.

#### When to Use This Pattern

Use `_build_order_expressions_with_mapping` (via a service-specific wrapper) when:

1. **Search queries include joins** to multiple tables (PersonDB, TeamDB, PositionDB)
2. **Frontend needs to sort by joined fields** (e.g., `order_by=second_name`)
3. **Default `_build_order_expressions` is insufficient** for field mapping needed

Use standard `_build_order_expressions` when:

1. **Only ordering by columns on the primary model** (no joins)
2. **Simple field-to-model mapping** isn't needed

#### Example: Player Team Tournament

See `src/player_team_tournament/db_services.py:176-198` for a complete implementation supporting ordering by:
- Primary table: `id`, `player_number`, `player_team_tournament_eesl_id`
- Joined tables: `first_name`, `second_name` (PersonDB), `team_title` (TeamDB), `position_title` (PositionDB)

### Common Pitfalls in Paginated Search

#### ❌ CRITICAL: Incorrect Count Query Pattern

**BUG**: Using `select_from(base_query)` instead of `select_from(base_query.subquery())` in count queries causes incorrect pagination when queries include joins.

```python
# ❌ WRONG - Causes incorrect counts with joins
count_stmt = select(func.count(func.distinct(ModelDB.id))).select_from(base_query)
```

**Why it fails**: When `base_query` includes joins (e.g., to PersonDB, TeamDB), `select_from(base_query)` counts all joined rows, not just the distinct model rows. This inflates `total_items` and causes incorrect `total_pages`.

```python
# ✅ CORRECT - Count distinct model rows after joins
count_stmt = select(func.count()).select_from(base_query.subquery())
```

**Impact**:
- Flag sport with 2 players showed 701 players (71 pages) instead of 2 players (1 page)
- Tournament with 43 players showed 699 players (70 pages) instead of 43 players (5 pages)

**Examples of this bug** (all fixed):
- `src/player/db_services.py:146` - `search_players_with_pagination_details()`
- `src/player_team_tournament/db_services.py:494` - `search_tournament_players_with_pagination()`
- `src/player_team_tournament/db_services.py:548` - `search_tournament_players_with_pagination_details()`

#### How to Implement Paginated Search When No Pattern Exists

When adding paginated search to a new domain:

1. **Check existing search implementations** in similar domains:
   ```bash
   grep -rn "func.count()" src/ --include="*.py" | grep "select_from"
   ```

2. **Follow the correct pattern** from existing working code:
   - `src/person/db_services.py` - `search_persons_with_pagination()`
   - `src/teams/db_services.py` - `search_teams_with_pagination()`
   - `src/matches/db_services.py` - `search_matches_with_pagination()`

3. **Key checklist for count query**:
   ```python
   # 1. Use subquery() to collapse joins
   base_query = select(ModelDB).join(...)
   count_stmt = select(func.count()).select_from(base_query.subquery())  # ✅ CORRECT

   # 2. Execute and handle null
   count_result = await session.execute(count_stmt)
   total_items = count_result.scalar() or 0

   # 3. Verify count matches actual data size
   # For debugging: check if base_query returns expected row count
   ```

4. **Test with joins**:
   ```python
   # Test case: Query with joins should not inflate count
   base_query = select(PlayerDB).join(PersonDB, ...).join(TeamDB, ...)
   # Count should equal number of distinct PlayerDB rows, NOT joined rows
   ```

5. **Add tests** for pagination accuracy:
   ```python
   async def test_pagination_with_joins_correct_count():
       # Create 10 players across 3 teams
       # Query with team join
       # Verify total_items == 10, not 30 (10 players × 3 teams)
   ```

  6. **Multiple Filter Support** (Player Team Tournament):
    - Supports combining `search_query` (person name) with `team_title` filter
    - Filters are applied with AND logic (must match both conditions)
    - Team title filter uses same ICU collation for international text handling
    - Example: `search=Иван&team_title=Динамо` returns players with name matching "Иван" AND team title matching "Динамо"

### Example: Person Domain

See `src/person/` for complete implementation:
- **Schema**: `PaginationMetadata`, `PaginatedPersonResponse`
- **Service**: `PersonServiceDB.search_persons_with_pagination()`
- **Router**: `PersonAPIRouter.get_all_persons_paginated_endpoint()`

### Test Database Setup

No special database setup is required for ilike-based search. Tests can use the standard test database setup.

**Important:** Search tests using ilike can run in parallel with no special requirements. Run with:
```bash
pytest tests/test_{domain}_search.py
```

### PostgreSQL pg_trgm Optimization (Optional Performance Enhancement)

The project includes optional `pg_trgm` extension for GIN index acceleration of ILIKE queries. This provides significant performance improvements for large datasets (>1000 rows).

#### Overview

- **pg_trgm** (trigram) extension provides trigram-based substring matching with GIN indexes
- **ILIKE + ICU collation**: Primary search approach (international text support)
- **GIN indexes**: Optional optimization for large datasets

#### Benefits

- **100-1800x performance improvement** on large datasets
- Substring matching anywhere in text (not just prefixes)
- Fast indexed lookups using trigrams
- Backward compatible with existing ILIKE queries

#### Trade-offs

- **Index size**: GIN indexes are ~3-4x larger than standard B-Tree indexes
- **Write performance**: 5-15% slower INSERT/UPDATE due to index maintenance
- **Small datasets**: PostgreSQL planner may prefer sequential scan (< 1000 rows)

#### Implementation Pattern

**1. Database Migration**:

```python
# alembic/versions/YYYY_MM_DD_HHMM-{hash}_add_pg_trgm_for_{domain}.py
def upgrade() -> None:
    # Install pg_trgm extension (only once per database)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # Create GIN indexes with gin_trgm_ops for ILIKE support
    op.execute(f"""
        CREATE INDEX ix_{table}_{field}_trgm
        ON {table} USING GIN ({field} gin_trgm_ops);
    """)

def downgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS ix_{table}_{field}_trgm;")
```

**2. No Code Changes Required** - Existing ILIKE queries automatically use pg_trgm indexes when beneficial

#### When to Use pg_trgm

**Use when:**
- Large datasets (>1000 rows) where full table scans are slow
- Search patterns like `%text%` (not just prefixes)
- Need substring matching anywhere in text
- Multi-language text with Unicode (Cyrillic, Latin, etc.)

**Avoid when:**
- Small datasets (<1000 rows) - sequential scan may be faster
- Short search terms (< 3 chars) - trigrams require 3+ chars
- Prefix-only search - standard B-Tree index is smaller
- Storage-constrained environments - GIN indexes are larger

#### Example: Person Domain

See `src/person/` for complete implementation:
- **Migration**: `alembic/versions/2026_01_06_1552-32e4ddf548e3_add_pg_trgm_extension_for_person_search.py`
- **Service**: `PersonServiceDB.search_persons_with_pagination()` in `src/person/db_services.py`

#### Verification

Check if indexes are being used:
```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT * FROM person WHERE first_name ILIKE '%query%';
```
- Look for `Bitmap Index Scan` or `Index Scan using ix_person_first_name_trgm`
- `Seq Scan` indicates index not used (expected for small datasets)

#### References

- **PostgreSQL pg_trgm docs**: https://www.postgresql.org/docs/current/pgtrgm.html
- **GIN Indexes**: https://www.postgresql.org/docs/current/gin.html
- **Full guide**: `PG_TRGM_SEARCH_OPTIMIZATION.md`

## Grouped Data Schemas and Career Endpoint Pattern

### Overview

When implementing endpoints that return pre-grouped historical data (e.g., player careers, event histories), use structured schemas to encapsulate grouping logic in the backend rather than frontend. This pattern separates concerns and provides optimized queries with single round-trip data loading.

### Pattern Components

#### 1. Base Assignment Schema

```python
# src/player/schemas.py
class TeamAssignmentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int | None = None
    team_title: str | None = None
    position_id: int | None = None
    position_title: str | None = None
    player_number: str | None = None
    tournament_id: int | None = None
    tournament_title: str | None = None
    season_id: int | None = None
    season_year: int | None = None
```

**Purpose**: Represents a single historical record (e.g., one player assignment to a team/tournament).

#### 2. Grouped Container Schemas

```python
class CareerByTeamSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: int | None = None
    team_title: str | None = None
    assignments: list[TeamAssignmentSchema] = Field(default_factory=list)


class CareerByTournamentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tournament_id: int | None = None
    tournament_title: str | None = None
    season_id: int | None = None
    season_year: int | None = None
    assignments: list[TeamAssignmentSchema] = Field(default_factory=list)
```

**Purpose**: Groups assignments by logical dimensions (team, tournament/season).

#### 3. Response Schema

```python
class PlayerCareerResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    career_by_team: list[CareerByTeamSchema] = Field(default_factory=list)
    career_by_tournament: list[CareerByTournamentSchema] = Field(default_factory=list)
```

**Purpose**: Wrapper containing multiple grouped views of the same data.

### Service Layer Implementation

#### Optimized Query with Eager Loading

```python
# src/player/db_services.py
@handle_service_exceptions(
    item_name=ITEM, operation="fetching player career data"
)
async def get_player_career(self, player_id: int) -> PlayerCareerResponseSchema:
    self.logger.debug(f"Get player career data for player_id:{player_id}")

    async with self.db.get_session_maker()() as session:
        # Single optimized query with all nested relationships
        stmt = (
            select(PlayerDB)
            .options(
                selectinload(PlayerDB.person),
                selectinload(PlayerDB.player_team_tournament).selectinload(
                    PlayerTeamTournamentDB.team
                ),
                selectinload(PlayerDB.player_team_tournament).selectinload(
                    PlayerTeamTournamentDB.position
                ),
                selectinload(PlayerDB.player_team_tournament).selectinload(
                    PlayerTeamTournamentDB.tournament
                ).selectinload(TournamentDB.season),
            )
            .where(PlayerDB.id == player_id)
        )

        result = await session.execute(stmt)
        player = result.scalars().one_or_none()

        if not player:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404,
                detail=f"Player id:{player_id} not found",
            )
```

#### Dictionary-Based Grouping Pattern

```python
        # Build assignment list
        assignments = [
            TeamAssignmentSchema(
                id=ptt.id,
                team_id=ptt.team_id,
                team_title=ptt.team.title if ptt.team else None,
                position_id=ptt.position_id,
                position_title=ptt.position.title if ptt.position else None,
                player_number=ptt.player_number,
                tournament_id=ptt.tournament_id,
                tournament_title=ptt.tournament.title if ptt.tournament else None,
                season_id=ptt.tournament.season_id if ptt.tournament else None,
                season_year=ptt.tournament.season.year if ptt.tournament and ptt.tournament.season else None,
            )
            for ptt in player.player_team_tournament
        ]

        # Group by team_id
        career_by_team_dict: dict[int | None, list[TeamAssignmentSchema]] = {}
        for assignment in assignments:
            team_id = assignment.team_id
            if team_id not in career_by_team_dict:
                career_by_team_dict[team_id] = []
            career_by_team_dict[team_id].append(assignment)

        # Group by (tournament_id, season_id) tuple
        career_by_tournament_dict: dict[
            tuple[int | None, int | None], list[TeamAssignmentSchema]
        ] = {}
        for assignment in assignments:
            tournament_id = assignment.tournament_id
            season_id = assignment.season_id
            key = (tournament_id, season_id)
            if key not in career_by_tournament_dict:
                career_by_tournament_dict[key] = []
            career_by_tournament_dict[key].append(assignment)

        # Build grouped responses with sorting
        career_by_team = sorted(
            [
                CareerByTeamSchema(
                    team_id=team_id,
                    team_title=(
                        assignments_by_team[0].team_title if assignments_by_team else None
                    ),
                    assignments=assignments_by_team,
                )
                for team_id, assignments_by_team in career_by_team_dict.items()
                if team_id is not None
            ],
            key=lambda x: x.team_title or "",
        )

        career_by_tournament = sorted(
            [
                CareerByTournamentSchema(
                    tournament_id=tournament_id,
                    tournament_title=(
                        assignments_by_tournament[0].tournament_title
                        if assignments_by_tournament
                        else None
                    ),
                    season_id=season_id,
                    season_year=(
                        assignments_by_tournament[0].season_year
                        if assignments_by_tournament
                        else None
                    ),
                    assignments=assignments_by_tournament,
                )
                for (
                    tournament_id,
                    season_id,
                ), assignments_by_tournament in career_by_tournament_dict.items()
                if tournament_id is not None
            ],
            key=lambda x: (x.season_year or 0),
            reverse=True,  # Newest first
        )

        return PlayerCareerResponseSchema(
            career_by_team=career_by_team,
            career_by_tournament=career_by_tournament,
        )
```

### Router Layer Implementation

```python
# src/player/views.py
@router.get("/id/{player_id}/career", response_model=PlayerCareerResponseSchema)
async def player_career_endpoint(player_id: int):
    self.logger.debug(f"Get player career for player_id:{player_id} endpoint")
    try:
        return await self.service.get_player_career(player_id)
    except HTTPException:
        raise
    except Exception as ex:
        self.logger.error(
            f"Error getting player career for player_id:{player_id} {ex}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error fetching player career",
        ) from ex
   ```

### Key Implementation Details

#### 1. Single Query with Nested `selectinload()`

- Chained `selectinload()` loads 4 relationship levels in one query
- Prevents N+1 query problems across team, position, tournament, season
- `selectinload()` preferred over `joinedload()` for many-to-many relationships

#### 2. Dictionary-Based Grouping

- Use Python dictionaries for O(1) grouping lookups
- Composite keys (tuples) for multi-dimensional grouping: `(tournament_id, season_id)`
- Filter out `None` values to exclude incomplete records

#### 3. Response Sorting

- **By team**: Alphabetical by `team_title`
- **By tournament/season**: Chronological descending (newest first) via `reverse=True`

#### 4. 404 Handling

- Service raises `HTTPException` with 404 when player not found
- Router re-raises HTTPExceptions, wraps others in 500 error

### When to Use This Pattern

**Use grouped data schemas when:**

- Frontend needs multiple views of the same historical data
- Grouping logic is complex or prone to errors
- Backend can optimize queries better than frontend
- Need consistent grouping across multiple clients

**Do NOT use when:**

- Data is flat and ungrouped (use standard schemas)
- Grouping is dynamic based on user input (frontend should handle)
- Simple one-level relationships suffice

### Example: Player Career Endpoint

**Endpoint**: `GET /api/players/id/{player_id}/career`

**Response**:
```json
{
  "career_by_team": [
    {
      "team_id": 1,
      "team_title": "FC Barcelona",
      "assignments": [
        {
          "id": 101,
          "team_id": 1,
          "team_title": "FC Barcelona",
          "position_id": 3,
          "position_title": "Forward",
          "player_number": "10",
          "tournament_id": 5,
          "tournament_title": "La Liga 2024",
          "season_id": 2,
          "season_year": 2024
        }
      ]
    }
  ],
  "career_by_tournament": [
    {
      "tournament_id": 5,
      "tournament_title": "La Liga 2024",
      "season_id": 2,
      "season_year": 2024,
      "assignments": [
        {
          "id": 101,
          "team_id": 1,
          "team_title": "FC Barcelona",
          "position_id": 3,
          "position_title": "Forward",
          "player_number": "10",
          "tournament_id": 5,
          "tournament_title": "La Liga 2024",
          "season_id": 2,
          "season_year": 2024
        }
      ]
    }
  ]
}
```

### Testing Guidelines

```python
# tests/test_player_service.py
async def test_get_player_career_success(player_with_assignments):
    player_id = player_with_assignments.id
    response = await player_service.get_player_career(player_id)

    assert isinstance(response, PlayerCareerResponseSchema)
    assert len(response.career_by_team) > 0
    assert len(response.career_by_tournament) > 0
    # Verify chronological ordering
    assert response.career_by_tournament[0].season_year >= response.career_by_tournament[-1].season_year

async def test_get_player_career_not_found():
    with pytest.raises(HTTPException) as exc_info:
        await player_service.get_player_career(999999)
    assert exc_info.value.status_code == 404
```

### References

- **Implementation**: `src/player/schemas.py`, `src/player/db_services.py`, `src/player/views.py`
- **Related Issues**: STAB-67, STAB-68, STAB-69
- **PR**: https://github.com/nevalions/statsboards-backend/pull/11

## WebSocket and Real-time

- Use existing `ws_manager` for connection management
- Follow event notification patterns in existing modules
- Test connection handling and reconnection scenarios
- Use Redis pub/sub for scalable event distribution
- Always clean up connections on disconnect
- WebSocket compression (permessage-deflate) is enabled for 10-20% bandwidth reduction
- Compression status is logged for each WebSocket connection for monitoring

## User Ownership and Privacy

Several core models support user ownership and privacy controls:

### Models with Ownership and Privacy

The following models include user ownership and privacy fields:

- **TournamentDB** - `user_id` (FK to user.id), `isprivate` (default: false)
- **PlayerDB** - `user_id` (FK to user.id), `isprivate` (default: false)
- **PersonDB** - `owner_user_id` (FK to user.id), `isprivate` (default: false)
- **MatchDB** - `user_id` (FK to user.id), `isprivate` (default: false)
- **TeamDB** - `user_id` (FK to user.id), `isprivate` (default: false)

### Field Details

#### user_id / owner_user_id

- **Type**: `Mapped[int]`
- **Foreign Key**: References `user.id` with `ON DELETE SET NULL`
- **Nullable**: Yes (allows items without specific owner)
- **Purpose**: Associates items with a specific user for access control

#### isprivate

- **Type**: `Mapped[bool]`
- **Default**: `False`
- **Server Default**: `"false"`
- **Nullable**: No
- **Purpose**: Allows users to hide their items from other users

### Model Patterns

```python
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import Base

if TYPE_CHECKING:
    from .user import UserDB

class ExampleDB(Base):
    __tablename__ = "example"
    __table_args__ = {"extend_existing": True}

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", name="fk_example_user", ondelete="SET NULL"),
        nullable=True,
    )

    isprivate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    user: Mapped["UserDB"] = relationship(
        "UserDB",
        back_populates="examples",
    )
```

### Usage Patterns

#### Filtering by User Ownership

```python
# Get only user's items
from src.core.models.tournament import TournamentDB
from sqlalchemy import select

async def get_user_tournaments(user_id: int, session: AsyncSession) -> list[TournamentDB]:
    stmt = select(TournamentDB).where(TournamentDB.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()
```

#### Combining Ownership with Privacy

```python
# Get user's items, excluding private ones (or including based on policy)
from src.core.models.player import PlayerDB

async def get_accessible_players(user_id: int, session: AsyncSession) -> list[PlayerDB]:
    stmt = select(PlayerDB).where(
        (PlayerDB.user_id == user_id) | (~PlayerDB.isprivate)
    )
    result = await session.execute(stmt)
    return result.scalars().all()
```

### Migration Notes

When adding user ownership to new models:

1. Add foreign key with explicit name: `name="fk_{table}_user"`
2. Use `ondelete="SET NULL"` to preserve records when user is deleted
3. Add `isprivate` column with `default=False` and `server_default="false"`
4. Add bidirectional relationship in UserDB
5. Include constraint names in migrations to avoid circular dependency issues

### Important Notes

- **PersonDB** uses `owner_user_id` instead of `user_id` to distinguish from authentication relationship
- All foreign keys to `user` table use `ON DELETE SET NULL` to preserve data integrity
- `isprivate` defaults to `false` to maintain backwards compatibility
- Foreign keys have explicit names to enable clean table drops without circular dependency errors

## General Principles

- Follow existing patterns rather than creating new ones
- Keep functions focused and single-responsibility
- Prefer composition over inheritance
- Use type hints everywhere for better IDE support
- Write tests before or immediately after implementing features
- Always run lint and test commands before considering a task complete
- Never hardcode credentials or secrets - use environment variables
- Use Pydantic Settings for configuration in `src/core/config.py`

## Configuration Validation

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

## Advanced Filtering Patterns

### Filtering by Relationship Exclusion

When you need to retrieve entities that are NOT related to another entity (e.g., persons not connected to a specific sport), use SQLAlchemy's `NOT EXISTS` subquery pattern. This is more performant than loading all entities and filtering in Python.

#### Example: Persons Not in Sport

```python
# Service method in src/person/db_services.py
from sqlalchemy import exists

@handle_service_exceptions(
    item_name=ITEM,
    operation="fetching persons not in sport",
    return_value_on_not_found=None,
)
async def get_persons_not_in_sport(
    self,
    sport_id: int,
    search_query: str | None = None,
    skip: int = 0,
    limit: int = 20,
    order_by: str = "second_name",
    order_by_two: str = "id",
    ascending: bool = True,
) -> PaginatedPersonResponse:
    async with self.db.get_session_maker()() as session:
        # Subquery to find persons who ARE in the sport
        subquery = select(PlayerDB.id).where(
            PlayerDB.person_id == PersonDB.id,
            PlayerDB.sport_id == sport_id,
        )

        # Query for persons NOT in the sport (NOT EXISTS)
        base_query = select(PersonDB).where(~exists(subquery))
        
        # Apply search filters if provided
        base_query = await self._apply_search_filters(
            base_query,
            [(PersonDB, "first_name"), (PersonDB, "second_name")],
            search_query,
        )

        # Count total results
        count_stmt = select(func.count()).select_from(base_query.subquery())
        count_result = await session.execute(count_stmt)
        total_items = count_result.scalar() or 0

        # Apply ordering and pagination
        order_expr, order_expr_two = await self._build_order_expressions(
            PersonDB, order_by, order_by_two, ascending, PersonDB.second_name, PersonDB.id
        )

        data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
        result = await session.execute(data_query)
        persons = result.scalars().all()

        return PaginatedPersonResponse(
            data=[PersonSchema.model_validate(p) for p in persons],
            metadata=PaginationMetadata(
                **await self._calculate_pagination_metadata(total_items, skip, limit),
            ),
        )
```

#### Endpoint Implementation

```python
# Router in src/person/views.py
@router.get(
    "/not-in-sport/{sport_id}",
    response_model=PaginatedPersonResponse,
)
async def get_persons_not_in_sport_endpoint(
    sport_id: int,
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    items_per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    order_by: str = Query("second_name", description="First sort column"),
    order_by_two: str = Query("id", description="Second sort column"),
    ascending: bool = Query(True, description="Sort order (true=asc, false=desc)"),
    search: str | None = Query(None, description="Search query for full-text search"),
):
    skip = (page - 1) * items_per_page
    response = await self.service.get_persons_not_in_sport(
        sport_id=sport_id,
        search_query=search,
        skip=skip,
        limit=items_per_page,
        order_by=order_by,
        order_by_two=order_by_two,
        ascending=ascending,
    )
    return response
```

#### Key Benefits

1. **Database-Level Filtering**: Uses `NOT EXISTS` subquery optimized by PostgreSQL
2. **Consistent Pagination**: Reuses `SearchPaginationMixin` for unified behavior
3. **Search Integration**: Works seamlessly with existing search functionality
4. **Performance**: Avoids loading unnecessary data, filtering at database level

#### Best Practices

- **Use `NOT EXISTS`** instead of `NOT IN` for better query planner optimization
- **Combine with search**: Apply search filters after the NOT EXISTS filter
- **Persons without players**: The NOT EXISTS pattern automatically includes entities without any related records (persons with no player entries)
- **Reuse mixins**: Always use `SearchPaginationMixin` methods for consistent pagination

### Pagination Metadata Consistency

All paginated endpoints MUST use the consistent `PaginationMetadata` schema from `src/core/schema_helpers.py`:

```python
class PaginationMetadata(BaseModel):
    page: int
    items_per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool
```

**Important Notes:**
- Count endpoints should return `{"total_items": count}` not `{"total": count}`
- All paginated responses must use this exact schema
- This ensures frontend consistency across all domains (Persons, Players, Matches, Teams)

### Example Use Cases

1. **Dropdown Options**: Filter available persons for adding to a team/sport
2. **Entity Exclusion**: Find entities not yet associated with a related entity
3. **Availability Checks**: Determine what entities can be added to specific relationships
