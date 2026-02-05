# Code Style Guidelines

## Import Organization

- Standard library imports first
- Third-party imports second
- Local application imports third
- Use `from typing import` for type hints at the top
- Use relative imports within domain modules (e.g., `from .schemas import ...`)
- Use absolute imports for cross-domain imports (e.g., `from src.core.models import ...`)

## Type Hints

- Use Python 3.11+ type hint syntax: `str | None` instead of `Optional[str]`
- Always annotate function parameters and return types
- Use `Annotated` for Pydantic field validation: `Annotated[str, Path(max_length=50)]`
- Use `TYPE_CHECKING` for circular import dependencies in models

## Conditional Statements

- **Use match/case for 5+ elif chains**:

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

- **Keep if/elif for simple logic** (2-4 branches, complex conditions, `isinstance()`)
- **Always include default case**: `case _:`
- **Prefer dictionaries for key-value mappings**:

```python
months = {"jan": "january", "feb": "february"}
return months.get(month_key)
```

## Naming Conventions

- **Classes**: PascalCase with descriptive suffixes (e.g., `TeamServiceDB`, `TeamSchema`, `TeamAPIRouter`)
- **Functions**: snake_case (e.g., `create_or_update_team`)
- **Variables**: snake_case (e.g., `team_id`, `tournament_id`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `ITEM = "TEAM"`)
- **Private methods**: Prefix with underscore when needed (e.g., `_validate_data`)

## Service Layer Pattern

- All service classes inherit from `BaseServiceDB`
- Initialize with database dependency: `super().__init__(database, TeamDB)`
- Use `self.logger` for structured logging
- Return database model objects, not dictionaries
- Raise `HTTPException` for client-facing errors
- Use `async/await` for all database operations
- **Use Service Registry for cross-service dependencies**:
  - Never directly import and instantiate other services
  - Access dependencies through `self.service_registry.get("service_name")`
  - Example: `team_service = self.service_registry.get("team")`
  - See `docs/SERVICE_LAYER_DECOUPLING.md` for details

## Router Pattern

- Inherit from `BaseRouter[SchemaType, CreateSchemaType, UpdateSchemaType]`
- Initialize with prefix and tags: `super().__init__("/api/teams", ["teams"], service)`
- Add custom endpoints after calling `super().route()`
- Use descriptive endpoint function names with `_endpoint` suffix

## Authorization Pattern

Use the `require_roles` dependency:

```python
from src.auth.dependencies import require_roles
from typing import Annotated

@router.post("/api/roles/")
async def create_role_endpoint(
    role_data: RoleSchemaCreate,
    _: Annotated[RoleDB, Depends(require_roles("admin"))],
) -> RoleSchema:
    return await service.create(role_data)
```

Key points:

- Use `require_roles("role1", "role2")` for role-based access
- Accepts multiple roles (user needs at least one)
- Uses service registry database for consistency
- Returns authenticated user with roles loaded

## Schema Patterns

- Inheritance: `TeamSchemaBase` → `TeamSchemaCreate` → `TeamSchema`
- `TeamSchemaUpdate` should have all fields optional
- Add `model_config = ConfigDict(from_attributes=True)` to output schemas
- Use Pydantic `Annotated` for validation constraints
- Keep response models separate from request models
- Add `from __future__ import annotations` at the top of schema files

### Shared Base Classes (src/core/shared_schemas.py)

**SponsorFieldsBase**:

```python
from src.core.shared_schemas import SponsorFieldsBase

class TeamSchemaBase(SponsorFieldsBase):
    title: str
    sport_id: int
```

**PrivacyFieldsBase**:

```python
from src.core.shared_schemas import PrivacyFieldsBase

class TeamSchemaBase(SponsorFieldsBase, PrivacyFieldsBase):
    title: str
    sport_id: int
```

**PlayerTeamTournamentBaseFields**:

```python
from src.core.shared_schemas import PlayerTeamTournamentBaseFields

class PlayerTeamTournamentWithDetailsSchema(PlayerTeamTournamentBaseFields):
    id: int
    first_name: str | None = None
    second_name: str | None = None
```

## Model Patterns

- Use `Mapped[type]` with `mapped_column()` for all columns
- Set `nullable=True` for optional fields
- Use `default` and `server_default` for default values
- Define relationships with proper `back_populates`
- Use `TYPE_CHECKING` block for forward references
- Include `__table_args__ = {"extend_existing": True}` in all models

## Creating New Models with Alembic

**Migration naming**: `YYYY_MM_DD_HHMM-{hash}_{snake_case_description}.py`

### One-to-One Relationships

```python
class ScoreboardDB(Base):
    __tablename__ = "scoreboard"
    __table_args__ = {"extend_existing": True}

    match_id: Mapped[int] = mapped_column(
        ForeignKey("match.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
    )

    matches: Mapped["MatchDB"] = relationship(
        "MatchDB",
        back_populates="match_scoreboard",
    )
```

### One-to-Many Relationships

```python
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

### Many-to-Many Relationships

```python
class UserDB(Base):
    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}

    roles: Mapped[list["RoleDB"]] = relationship(
        "RoleDB",
        secondary="user_role",
        back_populates="users",
    )
```

### Many-to-Many with Extra Columns

```python
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

### Self-Referencing Relationships

```python
class MatchDB(Base):
    __tablename__ = "match"

    team_a_id: Mapped[int] = mapped_column(ForeignKey("team.id", ondelete="CASCADE"))
    team_b_id: Mapped[int] = mapped_column(ForeignKey("team.id", ondelete="CASCADE"))

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

### Relationship Naming Conventions

| Relationship Type | Child Side (FK) | Parent Side (Collection) |
|-----------------|----------------|-------------------------|
| One-to-many | `sport_id: Mapped[int]` | `tournaments: Mapped[list["TournamentDB"]]` |
| Many-to-one | `sport: Mapped["SportDB"]` | - |
| One-to-one | `match_id: Mapped[int]` with `unique=True` | `match_scoreboard: Mapped["ScoreboardDB"]` |
| Many-to-many | Uses `secondary="association_table"` | Uses `secondary="association_table"` |

### Cascade Options

- `cascade="all, delete-orphan"` for parent-child
- `cascade="save-update, merge"` for many-to-many
- `passive_deletes=True` to rely on database-level CASCADE

### Foreign Key ON DELETE Options

- `ondelete="CASCADE"` for dependent records
- `ondelete="SET NULL"` for optional relationships
- No `ondelete` to restrict deletion

### Index Creation on Relationship Columns

```python
op.create_index(
    "ix_match_tournament_id_team_a_id_team_b_id",
    "match",
    ["tournament_id", "team_a_id", "team_b_id"],
)
```

Naming convention: `ix_{table_name}_{column_names_underscored}`.

## Forward References with TYPE_CHECKING

Purpose: break circular import dependencies while keeping type safety.

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .person import PersonDB

class UserDB(Base):
    person: Mapped["PersonDB"] = relationship("PersonDB", ...)
```

### Import Structure

```python
# 1. Standard library imports
from typing import TYPE_CHECKING

# 2. Third-party imports
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

# 3. Local imports
from src.core.models import Base

# 4. TYPE_CHECKING block
if TYPE_CHECKING:
    from .person import PersonDB

class UserDB(Base):
    ...
```

### Import Format Rules

- Models in same directory: relative imports (`from .person import PersonDB`)
- Models from mixins directory: double dots (`from ..season import SeasonDB`)
- Avoid absolute imports in TYPE_CHECKING blocks for same package models
- No aliases

### Empty TYPE_CHECKING Blocks

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

class TeamTournamentDB(Base):
    ...
```

### Relationship Type Hints

```python
person: Mapped["PersonDB"] = relationship("PersonDB", ...)
tournaments: Mapped[list["TournamentDB"]] = relationship("TournamentDB", ...)
```

### TYPE_CHECKING in Mixins

```python
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

if TYPE_CHECKING:
    from ..season import SeasonDB
    from ..sport import SportDB

class SeasonSportRelationMixin:
    @declared_attr
    def season_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("season.id", ondelete=cls._ondelete))

    @declared_attr
    def season(cls) -> Mapped["SeasonDB"]:
        return relationship("SeasonDB", back_populates=cls._season_back_populates)
```

### Why This Works

1. Runtime: imports are skipped
2. Type checking: imports execute
3. SQLAlchemy resolves string annotations

### Common Pitfalls to Avoid

```python
# BAD - direct imports cause circular import
from .person import PersonDB
person: Mapped[PersonDB] = relationship(PersonDB, ...)

# BAD - defeats purpose
if TYPE_CHECKING:
    from .person import PersonDB
person: Mapped[PersonDB] = relationship(PersonDB, ...)
```
