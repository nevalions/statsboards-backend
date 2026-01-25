# Schema Standardization Plan

## Overview

This document outlines a comprehensive plan for standardizing Pydantic schema patterns in the statsboards-backend project. The goal is to ensure consistency across all domains with clear naming conventions, schema hierarchies, and guidelines for when to use different schema types.

## Current State Analysis

### Existing Patterns

The codebase already uses several schema patterns consistently:

| Schema Type | Purpose | Examples |
|--------------|---------|----------|
| `*SchemaBase` | Base fields shared across schemas, inherited by Create/Update | `PersonSchemaBase`, `TeamSchemaBase`, `PlayerSchemaBase` |
| `*SchemaCreate` | Input validation for POST requests | `PersonSchemaCreate`, `TeamSchemaCreate` |
| `*SchemaUpdate` | Input validation for PATCH/PUT requests | Generated via `make_fields_optional()` |
| `*Schema` | Full response model with id (extends Create) | `PersonSchema`, `TeamSchema`, `MatchSchema` |
| `*WithDetailsSchema` | Response with nested relationships (flattened) | `PlayerWithDetailsSchema`, `TeamWithDetailsSchema`, `MatchWithDetailsSchema` |
| `*WithFullDetailsSchema` | Response with deeply nested relationships | `PlayerWithFullDetailsSchema`, `PlayerTeamTournamentWithFullDetailsSchema` |
| `*WithTitlesSchema` | Response with title fields (flattened) | `PlayerTeamTournamentWithTitles` |

### Shared Base Schemas

The following base schemas are defined in `src/core/shared_schemas.py`:

- **SponsorFieldsBase**: Sponsor relationships (`sponsor_line_id`, `main_sponsor_id`)
- **PrivacyFieldsBase**: Privacy and ownership (`isprivate`, `user_id`)
- **LogoFieldsBase**: Logo/photo URLs (`original_url`, `icon_url`, `webview_url`)
- **PlayerTeamTournamentBaseFields**: PTT base fields
- **PlayerTeamTournamentWithTitles**: PTT with related title fields

### Domain-Specific Examples

#### Player Domain
```python
# Base
PlayerSchemaBase(PrivacyFieldsBase)  # sport_id, person_id, player_eesl_id
PlayerSchemaCreate(PlayerSchemaBase)
PlayerSchema(PlayerSchemaCreate)  # + id

# Details
PlayerWithDetailsSchema(PlayerSchema)  # + first_name, second_name, player_team_tournaments[]
PlayerWithFullDetailsSchema(PlayerSchema)  # + person, sport, player_team_tournaments[]
```

#### Team Domain
```python
# Base
TeamSchemaBase(SponsorFieldsBase, PrivacyFieldsBase)  # title, city, sport_id, etc.
TeamSchemaCreate(TeamSchemaBase)
TeamSchema(TeamSchemaCreate)  # + id

# Details
TeamWithDetailsSchema(TeamSchema)  # + sport, main_sponsor, sponsor_line
```

#### Match Domain
```python
# Base
MatchSchemaBase(SponsorFieldsBase, PrivacyFieldsBase)  # match_date, team_a_id, etc.
MatchSchemaCreate(MatchSchemaBase)
MatchSchema(MatchSchemaCreate)  # + id

# Details
MatchWithDetailsSchema(MatchSchema)  # + team_a, team_b, tournament
```

#### Tournament Domain
```python
# Base
TournamentSchemaBase(SponsorFieldsBase, PrivacyFieldsBase)
TournamentSchemaCreate(TournamentSchemaBase)
TournamentSchema(TournamentSchemaCreate)  # + id

# Details
TournamentWithDetailsSchema(TournamentSchema)  # + season, sport, teams, main_sponsor, sponsor_line
```

## Proposed Standardization

### 1. Naming Convention Standards

**Rule:** All schema names must follow this pattern:

```
{Entity}{Purpose}
```

| Purpose | Suffix | Description | Example |
|----------|---------|-------------|----------|
| Base | `SchemaBase` | Base fields, no id, inherits shared bases | `PlayerSchemaBase` |
| Create | `SchemaCreate` | Input for POST, no id | `PlayerSchemaCreate` |
| Update | `SchemaUpdate` | Input for PATCH, all optional | `PlayerSchemaUpdate` |
| Base Response | `Schema` | Full response with id | `PlayerSchema` |
| With Details | `WithDetailsSchema` | Nested relationships (1-2 levels) | `PlayerWithDetailsSchema` |
| With Full Details | `WithFullDetailsSchema` | Deeply nested relationships (3+ levels) | `PlayerWithFullDetailsSchema` |
| With Titles | `WithTitlesSchema` | Flattened title fields | `PlayerTeamTournamentWithTitles` |
| List Item | `{Entity}ListItemSchema` | For list responses | `TeamListItemSchema` |

### 2. Schema Hierarchy Rules

**Every domain with relationships must have:**

1. **Base Schema** (`{Entity}SchemaBase`)
   - Inherits relevant shared bases
   - Contains only entity-specific fields
   - No `id` field
   - Uses `Field()` with descriptions and examples

2. **Create Schema** (`{Entity}SchemaCreate`)
   - Extends Base Schema
   - Pass-through (no additional fields)
   - Used for POST request bodies

3. **Update Schema** (`{Entity}SchemaUpdate`)
   - Generated via `make_fields_optional(BaseSchema)`
   - All fields optional
   - Used for PATCH request bodies

4. **Response Schema** (`{Entity}Schema`)
   - Extends Create Schema
   - Adds `id: int`
   - Has `model_config = ConfigDict(from_attributes=True)`
   - Used for single item responses

5. **With Details Schema** (`{Entity}WithDetailsSchema`)
   - **REQUIRED** if entity has 1+ direct relationships
   - Extends Response Schema
   - Adds nested schemas or flattened fields
   - Uses appropriate eager loading (joinedload/selectinload)

6. **With Full Details Schema** (`{Entity}WithFullDetailsSchema`)
   - **REQUIRED** if entity has 2+ levels of nested relationships
   - Extends Response Schema
   - Adds deeply nested schemas
   - Uses `Any` type for forward references in paginated responses
   - Uses chained eager loading

### 3. When to Use Each Schema Type

#### Base Schema (`{Entity}SchemaBase`)
**Use when:**
- Defining core entity fields
- Creating inheritance hierarchy
- Sharing fields across multiple schemas

**DO NOT:**
- Add `id` field (belongs in Response)
- Add relationship fields (belongs in WithDetails)

#### Create Schema (`{Entity}SchemaCreate`)
**Use when:**
- Validating POST request bodies
- Creating new entities

**DO NOT:**
- Add `id` field (server-generated)
- Add computed fields (created_at, updated_at)

#### Update Schema (`{Entity}SchemaUpdate`)
**Use when:**
- Validating PATCH request bodies
- Partial updates to existing entities

**DO NOT:**
- Require any fields (all optional)

#### Response Schema (`{Entity}Schema`)
**Use when:**
- Returning single entity after create/update
- Basic GET by ID endpoint
- List items where no relationships needed

**ALWAYS:**
- Include `id: int`
- Set `model_config = ConfigDict(from_attributes=True)`

#### With Details Schema (`{Entity}WithDetailsSchema`)
**Use when:**
- Entity has direct relationships (1:1, many:1)
- GET endpoint needs related data
- Avoiding N+1 queries for common access patterns

**Examples:**
- `TeamWithDetailsSchema`: Include `sport`, `main_sponsor`, `sponsor_line`
- `PlayerWithDetailsSchema`: Include `first_name`, `second_name` (from Person), `player_team_tournaments[]`
- `MatchWithDetailsSchema`: Include `team_a`, `team_b`, `tournament`

**Pattern:**
```python
class TeamWithDetailsSchema(TeamSchema):
    sport: SportSchema | None = Field(None, description="Sport with full details")
    main_sponsor: SponsorSchema | None = Field(None, description="Main sponsor with full details")
    sponsor_line: SponsorLineSchema | None = Field(None, description="Sponsor line with full details")
```

#### With Full Details Schema (`{Entity}WithFullDetailsSchema`)
**Use when:**
- Entity has 2+ levels of nested relationships
- Deeply nested data required (e.g., Player → Person → Addresses)
- Complex dashboards or detail pages

**Examples:**
- `PlayerWithFullDetailsSchema`: Include `person` (PersonSchema), `sport` (SportSchema), `player_team_tournaments[]`
- `TournamentWithFullDetailsSchema`: Include `season`, `sport`, `teams[]`, `main_sponsor`, `sponsor_line`

**Pattern:**
```python
class PlayerWithFullDetailsSchema(PlayerSchema):
    person: PersonSchema | None = Field(None, description="Person with full details")
    sport: SportSchema | None = Field(None, description="Sport with full details")
    player_team_tournaments: list[PlayerTeamTournamentWithTitles] = Field(
        default_factory=list,
        description="Player team tournament associations with nested details"
    )
```

**Important:** Use `Any` type for paginated responses to avoid Pydantic forward reference errors:
```python
class PlayerWithFullDetailsSchema(PlayerSchema):
    person: Any = Field(None, description="Person with full details")
    sport: Any = Field(None, description="Sport with full details")
    player_team_tournaments: list[Any] = Field(
        default_factory=list,
        description="Player team tournament associations with nested details"
    )
```

### 4. Joined vs Flattened Schemas

#### Joined Schemas (Nested Objects)
**Use when:**
- Need full nested object with all fields
- Client needs complete related data
- Object may be updated independently
- Example: `TeamWithDetailsSchema.sport` is a full `SportSchema`

**Benefits:**
- Type-safe access to all nested fields
- Clear object boundaries
- Easy to validate complete objects

**Example:**
```python
class TeamWithDetailsSchema(TeamSchema):
    sport: SportSchema | None = None  # Full Sport object
```

#### Flattened Schemas (Title Fields)
**Use when:**
- Only need display fields (title, name)
- Reducing payload size
- Read-only access to related data
- Example: `PlayerTeamTournamentWithTitles` has `team_title`, `position_title`

**Benefits:**
- Smaller response payloads
- No nested objects to navigate
- Faster serialization

**Example:**
```python
class PlayerTeamTournamentWithTitles(BaseModel):
    team_id: int | None = None
    team_title: str | None = None  # Flattened from Team.title
    position_id: int | None = None
    position_title: str | None = None  # Flattened from Position.title
```

### 5. Pagination Standards

**Every list response must use:**

```python
from src.core.schema_helpers import PaginationMetadata

class Paginated{Entity}Response(BaseModel):
    data: list[{Entity}Schema]
    metadata: PaginationMetadata
```

**For detail schemas:**
```python
class Paginated{Entity}WithDetailsResponse(BaseModel):
    data: list[{Entity}WithDetailsSchema]
    metadata: PaginationMetadata

class Paginated{Entity}WithFullDetailsResponse(BaseModel):
    data: list[{Entity}WithFullDetailsSchema]
    metadata: PaginationMetadata
```

**PaginationMetadata fields:**
- `page`: Current page (1-based)
- `items_per_page`: Items per page
- `total_items`: Total items across all pages
- `total_pages`: Total pages available
- `has_next`: Whether there is a next page
- `has_previous`: Whether there is a previous page

### 6. Search Integration Standards

**Search endpoints must:**

1. Use `SearchPaginationMixin` from `src/core/models/mixins/search_pagination_mixin.py`
2. Support standard query parameters:
   - `search`: Search query string
   - `page`: Page number (1-based)
   - `items_per_page`: Items per page (max 100)
   - `order_by`: First sort column
   - `order_by_two`: Second sort column
   - `ascending`: Sort order (true=asc, false=desc)
3. Use ICU collation: `.collate("en-US-x-icu")` for case-insensitive search
4. Apply appropriate eager loading strategy

**Search method pattern:**
```python
async def search_{entity_lower}_with_details_pagination(
    self,
    search_query: str | None = None,
    page: int = 1,
    items_per_page: int = 20,
    order_by: str = "title",
    order_by_two: str = "id",
    ascending: bool = True,
    **filters,
) -> Paginated{Entity}WithDetailsResponse:
    skip = (page - 1) * items_per_page

    async with self.db.get_session_maker()() as session:
        base_query = select({Entity}DB).options(
            # Eager load based on schema type
            selectinload({Entity}DB.relationships),
        )

        # Apply search filters
        base_query = await self._apply_search_filters(
            base_query,
            search_fields=[({Entity}DB, "title")],
            search_query=search_query,
        )

        # Apply other filters
        if filter_field:
            base_query = base_query.where({Entity}DB.filter_field == filter_value)

        # Get total count
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_items = (await session.execute(count_stmt)).scalar() or 0

        # Order and paginate
        order_expr, order_expr_two = await self._build_order_expressions(
            {Entity}DB, order_by, order_by_two, ascending,
            {Entity}DB.id, {Entity}DB.title  # defaults
        )
        data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(items_per_page)

        result = await session.execute(data_query)
        items = result.scalars().all()

        return Paginated{Entity}WithDetailsResponse(
            data=[{Entity}WithDetailsSchema.model_validate(item) for item in items],
            metadata=PaginationMetadata(
                page=page,
                items_per_page=items_per_page,
                total_items=total_items,
                total_pages=ceil(total_items / items_per_page) if items_per_page > 0 else 0,
                has_next=skip + items_per_page < total_items,
                has_previous=skip > 0,
            ),
        )
```

### 7. Eager Loading Guidelines

**joinedload**: Use for single relationships (1:1, many:1)
```python
stmt = select(TeamDB).options(
    joinedload(TeamDB.main_sponsor),  # Team has one main sponsor
)
```

**selectinload**: Use for collection relationships (1:many, many:many)
```python
stmt = select(TournamentDB).options(
    selectinload(TournamentDB.teams),  # Tournament has many teams
)
```

**Chained loading**: For nested relationships
```python
stmt = select(PlayerDB).options(
    selectinload(PlayerDB.player_team_tournaments)
    .selectinload(PlayerTeamTournamentDB.team)  # Nested: PTT → Team
    .selectinload(PlayerTeamTournamentDB.tournament),  # Nested: PTT → Tournament
)
```

### 8. Common Patterns and Anti-Patterns

#### ✅ DO: Use Inheritance Properly
```python
class PlayerSchemaBase(PrivacyFieldsBase):
    sport_id: int | None = Field(None, examples=[1])
    person_id: int | None = Field(None, examples=[1])

class PlayerSchemaCreate(PlayerSchemaBase):
    pass  # No changes, just for clarity

class PlayerSchema(PlayerSchemaCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., examples=[1])

class PlayerWithDetailsSchema(PlayerSchema):
    first_name: str | None = Field(None, description="Person's first name")
    second_name: str | None = Field(None, description="Person's second name")
```

#### ✅ DO: Use Field Descriptions
```python
class PlayerSchemaBase(PrivacyFieldsBase):
    sport_id: int = Field(..., description="Sport ID this player belongs to", examples=[1])
    person_id: int = Field(..., description="Person ID for this player", examples=[1])
```

#### ✅ DO: Use Default Factory for Lists
```python
class PlayerWithFullDetailsSchema(PlayerSchema):
    player_team_tournaments: list[PlayerTeamTournamentWithTitles] = Field(
        default_factory=list,  # ✅ Use default_factory
        description="Player team tournament associations"
    )
```

#### ❌ DO NOT: Use Mutable Default Args
```python
class PlayerWithFullDetailsSchema(PlayerSchema):
    player_team_tournaments: list[PlayerTeamTournamentWithTitles] = Field(
        default=[],  # ❌ Bad - mutable default
        description="Player team tournament associations"
    )
```

#### ❌ DO NOT: Mix Responsibilities
```python
class PlayerWithDetailsSchema(PlayerSchema):
    # ❌ Bad - adding database logic to schema
    def get_active_teams(self):
        return [ptt for ptt in self.player_team_tournaments if ptt.is_active]
```

## Implementation Checklist

### For Each Domain

- [ ] Base schema exists (`{Entity}SchemaBase`)
  - [ ] Inherits appropriate shared bases
  - [ ] Contains only entity-specific fields
  - [ ] No `id` field
  - [ ] All fields have descriptions and examples

- [ ] Create schema exists (`{Entity}SchemaCreate`)
  - [ ] Extends Base schema
  - [ ] No additional fields (pass-through)

- [ ] Update schema exists (`{Entity}SchemaUpdate`)
  - [ ] Generated via `make_fields_optional(BaseSchema)`

- [ ] Response schema exists (`{Entity}Schema`)
  - [ ] Extends Create schema
  - [ ] Has `id: int` field
  - [ ] Has `model_config = ConfigDict(from_attributes=True)`

- [ ] WithDetails schema exists (`{Entity}WithDetailsSchema`)
  - [ ] Required if entity has relationships
  - [ ] Extends Response schema
  - [ ] Includes nested schemas or flattened fields
  - [ ] Uses `None` for optional relationships

- [ ] WithFullDetails schema exists (`{Entity}WithFullDetailsSchema`)
  - [ ] Required if entity has 2+ level relationships
  - [ ] Extends Response schema
  - [ ] Uses `Any` type for forward references in paginated responses

- [ ] Paginated responses exist
  - [ ] `Paginated{Entity}Response`
  - [ ] `Paginated{Entity}WithDetailsResponse`
  - [ ] `Paginated{Entity}WithFullDetailsResponse`

- [ ] Search endpoints exist
  - [ ] `/with-details/paginated` endpoint
  - [ ] `/with-full-details/paginated` endpoint (if WithFullDetails exists)
  - [ ] Uses `SearchPaginationMixin`
  - [ ] Supports standard query params
  - [ ] Uses appropriate eager loading

## Domains Requiring Standardization

Based on current implementation analysis, the following domains need standardization:

### ✅ Already Compliant
- Person (Base, Create, Update, Response, WithDetails)
- Player (Base, Create, Update, Response, WithDetails, WithFullDetails)
- Team (Base, Create, Update, Response, WithDetails)
- Tournament (Base, Create, Update, Response, WithDetails)
- Match (Base, Create, Update, Response, WithDetails)
- PlayerTeamTournament (Base, Create, Update, Response, WithDetails, WithFullDetails)
- Sport (Base, Create, Update, Response)
- Season (Base, Create, Update, Response)
- Sponsor (Base, Create, Update, Response)
- SponsorLine (Base, Create, Update, Response)
- Scoreboard (Base, Create, Update, Response)
- GameClock (Base, Create, Update, Response)
- PlayClock (Base, Create, Update, Response)
- Position (Base, Create, Update, Response)
- FootballEvent (Base, Create, Update, Response)
- MatchData (Base, Create, Update, Response)
- SponsorSponsorLineConnection (Base, Create, Update, Response)

### ⚠️ Needs Review
The following domains need review to ensure compliance with standards:

1. **Users** - Check if relationships need WithDetails schemas
2. **Seasons** - Check if needs WithDetails for tournaments
3. **Positions** - Check if needs WithDetails for player_team_tournaments
4. **SponsorLines** - Check if needs WithDetails for sponsors
5. **FootballEvents** - Check if needs WithDetails for matches/players

## Migration Plan

### Phase 1: Documentation and Standards (Week 1)
- [x] Analyze current implementation
- [x] Research best practices
- [ ] Create this standardization document
- [ ] Add schema examples to docs
- [ ] Review with team

### Phase 2: Domain Review and Gap Analysis (Week 2)
- [ ] Audit all domains for compliance
- [ ] Identify missing WithDetails schemas
- [ ] Identify missing WithFullDetails schemas
- [ ] Identify missing search endpoints
- [ ] Create Linear issues for each domain

### Phase 3: Schema Implementation (Week 3-4)
- [ ] Implement missing WithDetails schemas
- [ ] Implement missing WithFullDetails schemas
- [ ] Update existing schemas to follow conventions
- [ ] Add field descriptions to all schemas
- [ ] Ensure all schemas use `from_attributes=True`

### Phase 4: Service and View Updates (Week 5-6)
- [ ] Add search methods for all domains
- [ ] Add search endpoints for all domains
- [ ] Update existing search methods to use standard pattern
- [ ] Ensure consistent eager loading
- [ ] Add pagination wrappers

### Phase 5: Testing and Validation (Week 7)
- [ ] Write tests for new schemas
- [ ] Write tests for search endpoints
- [ ] Test eager loading strategies
- [ ] Validate OpenAPI schema generation
- [ ] Performance test search endpoints

### Phase 6: Documentation Updates (Week 8)
- [ ] Update COMBINED_SCHEMAS.md
- [ ] Update DEVELOPMENT_GUIDELINES.md
- [ ] Add schema creation checklist
- [ ] Add search implementation checklist
- [ ] Create quick reference guide

## Code Templates

### Template: Domain Schema File

```python
"""{Entity} schemas definition."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from src.core.schema_helpers import PaginationMetadata, make_fields_optional
from src.core.shared_schemas import {RelevantSharedBases}

if TYPE_CHECKING:
    from src.{other_domain}.schemas import {OtherDomain}Schema
    from src.{related_domain}.schemas import {RelatedDomain}Schema


class {Entity}SchemaBase({SharedBase1}, {SharedBase2}):
    """Base fields for {entity} entity."""
    field1: type1 = Field(..., description="Description", examples=[...])
    field2: type2 = Field(..., description="Description", examples=[...])


{Entity}SchemaUpdate = make_fields_optional({Entity}SchemaBase)


class {Entity}SchemaCreate({Entity}SchemaBase):
    """Schema for creating {entity}."""
    pass


class {Entity}Schema({Entity}SchemaCreate):
    """Full {entity} response with id."""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., examples=[1])


class {Entity}WithDetailsSchema({Entity}Schema):
    """{Entity} with nested relationships."""
    related1: {RelatedDomain}Schema | None = Field(
        None,
        description="Related entity with full details"
    )
    related2: list[{OtherDomain}Schema] = Field(
        default_factory=list,
        description="List of related entities"
    )


class {Entity}WithFullDetailsSchema({Entity}Schema):
    """{Entity} with deeply nested relationships."""
    person: Any = Field(None, description="Person with full details")
    related_deep: Any = Field(None, description="Deeply nested relation")


class Paginated{Entity}Response(BaseModel):
    """Paginated {entity} list response."""
    data: list[{Entity}Schema]
    metadata: PaginationMetadata


class Paginated{Entity}WithDetailsResponse(BaseModel):
    """Paginated {entity} list with details response."""
    data: list[{Entity}WithDetailsSchema]
    metadata: PaginationMetadata


class Paginated{Entity}WithFullDetailsResponse(BaseModel):
    """Paginated {entity} list with full details response."""
    data: list[{Entity}WithFullDetailsSchema]
    metadata: PaginationMetadata
```

## References

### Internal Documentation
- [COMBINED_SCHEMAS.md](COMBINED_SCHEMAS.md) - Existing combined schemas guide
- [DEVELOPMENT_GUIDELINES.md](DEVELOPMENT_GUIDELINES.md) - Development patterns and best practices
- [SERVICE_LAYER_DECOUPLING.md](SERVICE_LAYER_DECOUPLING.md) - Service layer architecture

### External Resources
- [FastAPI Response Models](https://fastapi.tiangolo.com/tutorial/response-model/) - Official FastAPI docs
- [Pydantic Models](https://docs.pydantic.dev/latest/concepts/models/) - Official Pydantic docs
- [FastAPI Nested Models](https://fastapi.tiangolo.com/tutorial/body-nested-models/) - Nested model patterns
- [Pydantic Best Practices](https://github.com/zhanymkanov/fastapi-best-practices) - Community best practices

## Appendix: Quick Reference

### Schema Decision Tree

```
Does entity have relationships?
├─ No → {Entity}SchemaBase, {Entity}SchemaCreate, {Entity}Schema
└─ Yes → Does it have 1-level relationships?
    ├─ Yes → {Entity}WithDetailsSchema
    │          └─ Use joinedload/selectinload for eager loading
    └─ Does it have 2+ level relationships?
        ├─ Yes → {Entity}WithFullDetailsSchema
        │         └─ Use Any type for forward references
        │         └─ Use chained eager loading
        └─ Maybe → Consider flattened fields for performance
```

### Field Checklist

For every schema field:
- [ ] Has appropriate type annotation
- [ ] Has description parameter
- [ ] Has examples parameter (for user-facing fields)
- [ ] Has `| None` if optional
- [ ] Has default value if optional and has default
- [ ] Uses `Field(default_factory=list)` for list defaults
- [ ] Uses `Annotated` with `Path` for string constraints

### Eager Loading Decision Tree

```
Relationship type?
├─ Single (1:1, many:1) → joinedload
└─ Collection (1:many, many:many) → selectinload

Need to go deeper?
├─ Yes → Chain with .selectinload() or .joinedload()
└─ No → Single level is sufficient
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-17  
**Next Review:** 2025-02-17
