# Combined Pydantic Schemas Guide

## Overview

This guide explains how to use combined Pydantic schemas that include nested relationship data, and how to create new complex schemas when needed.

Combined schemas provide full nested objects instead of just foreign key IDs, making API responses richer and more complete.

## Available Combined Schemas

### Match Schemas

| Schema | Description | Relationships Included |
|--------|-------------|------------------------|
| `MatchSchema` | Basic match with FK IDs | `team_a_id`, `team_b_id`, `tournament_id` |
| `MatchWithDetailsSchema` | Match with nested team/tournament objects | `team_a`, `team_b`, `tournament`, `main_sponsor`, `sponsor_line` |

**Example Response:**
```json
{
  "id": 1,
  "match_date": "2024-01-15T15:00:00Z",
  "week": 1,
  "team_a": {
    "id": 1,
    "title": "Manchester United",
    "city": "Manchester",
    "team_color": "#DA291C"
  },
  "team_b": {
    "id": 2,
    "title": "Liverpool",
    "city": "Liverpool",
    "team_color": "#C8102E"
  },
  "tournament": {
    "id": 1,
    "title": "Premier League",
    "year": 2024
  }
}
```

### Team Schemas

| Schema | Description | Relationships Included |
|--------|-------------|------------------------|
| `TeamSchema` | Basic team with FK IDs | `sport_id`, `main_sponsor_id`, `sponsor_line_id` |
| `TeamWithDetailsSchema` | Team with nested sport/sponsor objects | `sport`, `main_sponsor`, `sponsor_line` |

### Tournament Schemas

| Schema | Description | Relationships Included |
|--------|-------------|------------------------|
| `TournamentSchema` | Basic tournament with FK IDs | `season_id`, `sport_id`, `main_sponsor_id`, `sponsor_line_id` |
| `TournamentWithDetailsSchema` | Tournament with nested objects | `season`, `sport`, `teams[]`, `main_sponsor`, `sponsor_line` |

### Player Schemas

| Schema | Description | Relationships Included |
|--------|-------------|------------------------|
| `PlayerSchema` | Basic player with FK IDs | `sport_id`, `person_id` |
| `PlayerWithDetailsSchema` | Player with person and sport | `person`, `sport`, `player_team_tournaments[]` (flat) |
| `PlayerWithFullDetailsSchema` | Player with fully nested PTTs | `person`, `sport`, `player_team_tournaments[]` (nested) |

### PlayerTeamTournament Schemas

| Schema | Description | Relationships Included |
|--------|-------------|------------------------|
| `PlayerTeamTournamentSchema` | Basic PTT with FK IDs | `player_id`, `team_id`, `tournament_id`, `position_id` |
| `PlayerTeamTournamentWithDetailsSchema` | PTT with flattened fields | `team_title`, `position_title` |
| `PlayerTeamTournamentWithFullDetailsSchema` | PTT with nested objects | `team`, `tournament`, `position` |

## API Endpoints

### Match Endpoints

```bash
# Get match with FK IDs only
GET /api/matches/{id}/

# Get match with nested team, tournament, sponsor details
GET /api/matches/{id}/with-details/
```

### Team Endpoints

```bash
# Get team with FK IDs only
GET /api/teams/{id}/

# Get team with nested sport, sponsor details
GET /api/teams/{id}/with-details/
```

### Tournament Endpoints

```bash
# Get tournament with FK IDs only
GET /api/tournaments/{id}/

# Get tournament with nested season, sport, teams, sponsors
GET /api/tournaments/{id}/with-details/
```

## Usage Examples

### Frontend Example (JavaScript/TypeScript)

```typescript
// Fetch match with full details
const response = await fetch('/api/matches/123/with-details/');
const match: MatchWithDetailsSchema = await response.json();

// Access nested data directly
console.log(match.team_a.title);  // "Manchester United"
console.log(match.team_b.title);  // "Liverpool"
console.log(match.tournament.title);  // "Premier League"

// Display team logos
<img src={match.team_a.team_logo_url} />
<img src={match.team_b.team_logo_url} />
```

### Frontend Example (React)

```tsx
function MatchCard({ matchId }: { matchId: number }) {
  const { data: match, isLoading } = useQuery({
    queryKey: ['match', matchId, 'details'],
    queryFn: () => fetch(`/api/matches/${matchId}/with-details/`).then(r => r.json())
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="match-card">
      <div className="team-a">
        <img src={match.team_a.team_logo_url} alt={match.team_a.title} />
        <h3>{match.team_a.title}</h3>
      </div>
      <div className="vs">vs</div>
      <div className="team-b">
        <img src={match.team_b.team_logo_url} alt={match.team_b.title} />
        <h3>{match.team_b.title}</h3>
      </div>
      <div className="tournament">
        <span>{match.tournament.title}</span>
      </div>
    </div>
  );
}
```

### Frontend Example (Vue)

```vue
<template>
  <div v-if="match" class="tournament-card">
    <h2>{{ tournament.title }}</h2>
    <p>Season: {{ tournament.season.year }}</p>
    <p>Sport: {{ tournament.sport.title }}</p>

    <div class="teams">
      <div v-for="team in tournament.teams" :key="team.id" class="team">
        <img :src="team.team_logo_url" :alt="team.title" />
        <h3>{{ team.title }}</h3>
      </div>
    </div>

    <div v-if="tournament.main_sponsor" class="sponsor">
      <img :src="tournament.main_sponsor.logo_url" alt="Sponsor" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const tournament = ref(null);

onMounted(async () => {
  tournament.value = await fetch('/api/tournaments/1/with-details/')
    .then(r => r.json());
});
</script>
```

### Backend Service Example

```python
from src.matches.db_services import MatchServiceDB
from src.matches.schemas import MatchWithDetailsSchema

async def get_match_for_display(match_id: int) -> MatchWithDetailsSchema:
    service = MatchServiceDB(db)
    match_db = await service.get_match_with_details(match_id)
    return MatchWithDetailsSchema.model_validate(match_db)
```

## Creating New Complex Schemas

### Step 1: Identify Relationships

Determine which relationships to include in your new schema:

```python
# Example: Want to add SponsorWithMatches schema
# Relationships to include: matches[] with team_a, team_b
```

### Step 2: Define the Schema

Create a new schema file or add to existing one:

```python
from typing import TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, Field
from src.core.schema_helpers import PaginationMetadata

# Import related schemas inside TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from src.matches.schemas import MatchSchema
    from src.teams.schemas import TeamSchema

class SponsorWithMatchesSchema(SponsorSchema):
    """Extended sponsor schema with full match details."""
    matches: list["MatchSchema"] = Field(
        default_factory=list,
        description="Matches sponsored by this sponsor"
    )

class PaginatedSponsorWithMatchesResponse(BaseModel):
    """Paginated response with sponsor and match details."""
    data: list[SponsorWithMatchesSchema]
    metadata: PaginationMetadata
```

### Step 3: Add Service Method with Eager Loading

Add a method to fetch data with appropriate eager loading strategy:

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

class SponsorServiceDB(BaseServiceDB):
    async def get_sponsor_with_matches(self, sponsor_id: int) -> SponsorDB | None:
        """Get sponsor with full match details including teams."""
        async with self.db.async_session() as session:
            stmt = (
                select(SponsorDB)
                .where(SponsorDB.id == sponsor_id)
                .options(
                    # Use selectinload for collections (1:many, m2m)
                    selectinload(SponsorDB.matches)
                    # Chain nested relationships
                    .selectinload(SponsorDB.matches)
                    .joinedload(MatchDB.team_a),  # Single relationship - use joinedload
                    .joinedload(MatchDB.team_b),
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_sponsors_with_matches_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> PaginatedSponsorWithMatchesResponse:
        """Get sponsors with matches, paginated."""
        from src.sponsors.schemas import SponsorWithMatchesSchema

        async with self.db.async_session() as session:
            base_query = select(SponsorDB).options(
                selectinload(SponsorDB.matches)
                .selectinload(MatchDB.team_a)
                .selectinload(MatchDB.team_b),
            )

            # Count total
            count_stmt = select(func.count()).select_from(base_query.subquery())
            count_result = await session.execute(count_stmt)
            total_items = count_result.scalar() or 0

            # Fetch paginated data
            data_query = base_query.offset(skip).limit(limit)
            result = await session.execute(data_query)
            sponsors = result.scalars().all()

            return PaginatedSponsorWithMatchesResponse(
                data=[SponsorWithMatchesSchema.model_validate(s) for s in sponsors],
                metadata=PaginationMetadata(
                    page=(skip // limit) + 1,
                    items_per_page=limit,
                    total_items=total_items,
                    total_pages=(total_items + limit - 1) // limit,
                    has_next=skip + limit < total_items,
                    has_previous=skip > 0,
                ),
            )
```

### Step 4: Add API Endpoint

```python
from fastapi import HTTPException
from src.sponsors.schemas import SponsorWithMatchesSchema
from src.sponsors.db_services import SponsorServiceDB

class SponsorAPIRouter(BaseRouter):
    def route(self):
        router = super().route()

        @router.get(
            "/{sponsor_id}/with-matches/",
            response_model=SponsorWithMatchesSchema,
            summary="Get sponsor with matches",
            description="Retrieves a sponsor with all matches including team details.",
        )
        async def get_sponsor_with_matches_endpoint(sponsor_id: int):
            sponsor = await self.service.get_sponsor_with_matches(sponsor_id)
            if sponsor is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Sponsor id({sponsor_id}) not found",
                )
            return SponsorWithMatchesSchema.model_validate(sponsor)

        return router
```

## Eager Loading Strategy Guide

Choosing the right eager loading strategy is critical for performance:

### joinedload

**Use for:** Single relationships (1:1, many:1)

```python
stmt = select(TeamDB).options(
    joinedload(TeamDB.sport),  # Team has one sport
    joinedload(TeamDB.main_sponsor),  # Team has one main sponsor
)
```

**Why:**
- Single SQL query with JOIN
- Faster for single object fetching
- No additional queries

### selectinload

**Use for:** Collection relationships (1:many, m2m)

```python
stmt = select(TournamentDB).options(
    selectinload(TournamentDB.teams),  # Tournament has many teams
    selectinload(TournamentDB.matches),  # Tournament has many matches
)
```

**Why:**
- Two queries (one for parent, one for children)
- Avoids Cartesian product explosion
- More efficient for large collections

### Combined Strategy

For complex nested relationships:

```python
stmt = select(MatchDB).options(
    # Load team_a and its nested sport (single relationships)
    joinedload(MatchDB.team_a).joinedload(TeamDB.sport),
    # Load team_b and its nested sport (single relationships)
    joinedload(MatchDB.team_b).joinedload(TeamDB.sport),
    # Load tournament and its teams (collection relationship)
    selectinload(MatchDB.tournaments).selectinload(TournamentDB.teams),
)
```

## Best Practices

### 1. Avoid Circular Imports

Use `TYPE_CHECKING` and string type hints:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.other_module.schemas import OtherSchema

class MySchema(BaseModel):
    related: "OtherSchema" | None = None
```

### 2. Always Use `from_attributes=True`

For schemas that will validate SQLAlchemy models:

```python
class MySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

This enables Pydantic v2's `model_validate()` to work with ORM objects.

### 3. Use Field Descriptions

Add descriptions to all new fields for better OpenAPI documentation:

```python
class MatchWithDetailsSchema(MatchSchema):
    team_a: TeamSchema | None = Field(
        None,
        description="Team A with full details including sport and sponsor"
    )
```

### 4. Create Pagination Wrappers

For all list responses:

```python
class PaginatedMatchWithDetailsResponse(BaseModel):
    data: list[MatchWithDetailsSchema]
    metadata: PaginationMetadata
```

### 5. Separate Base and Details Schemas

Keep basic FK-only schemas for CRUD operations:

- `MatchSchema` - For POST/PUT (IDs only)
- `MatchWithDetailsSchema` - For GET with full data

### 6. Use Default Factories for Lists

Avoid mutable default arguments:

```python
# ❌ Bad
class BadSchema(BaseModel):
    items: list[ItemSchema] = []

# ✅ Good
class GoodSchema(BaseModel):
    items: list[ItemSchema] = Field(default_factory=list)
```

### 7. Annotate Optional Relationships

Use `| None` for optional relationships:

```python
class TeamWithDetailsSchema(TeamSchema):
    sport: SportSchema | None = Field(None, description="Sport with full details")
    main_sponsor: SponsorSchema | None = Field(None, description="Main sponsor (optional)")
```

## Performance Considerations

### N+1 Query Problem

Without eager loading, this causes N+1 queries:

```python
# ❌ Bad - Causes N+1 queries
matches = await session.execute(select(MatchDB)).scalars().all()
for match in matches:
    print(match.team_a.title)  # Separate query for each match!
```

With eager loading, single query:

```python
# ✅ Good - Single query
stmt = select(MatchDB).options(joinedload(MatchDB.team_a))
matches = (await session.execute(stmt)).scalars().all()
for match in matches:
    print(match.team_a.title)  # No additional queries!
```

### When to Use Basic vs Combined Schemas

**Use Basic Schema (`MatchSchema`) when:**
- Creating/Updating resources (POST/PUT)
- Listing resources where you only need minimal info
- Building admin interfaces with separate detail pages
- Mobile apps with bandwidth constraints

**Use Combined Schema (`MatchWithDetailsSchema`) when:**
- Displaying full resource details
- Building dashboards that show related data
- Avoiding multiple API calls
- Desktop/tablet web applications

### Pagination for Large Collections

For endpoints that return large collections (like `teams` in `TournamentWithDetailsSchema`), consider:

1. Adding pagination limits
2. Making collections optional with query params
3. Creating separate endpoints for nested collections

```python
# Option 1: Limit nested collection
class TournamentWithDetailsSchema(TournamentSchema):
    teams: list[TeamSchema] = Field(
        default_factory=list,
        description="First 50 teams in this tournament (use paginated endpoint for more)"
    )

# Option 2: Query param to include
@router.get("/tournaments/{id}/")
async def get_tournament_endpoint(
    tournament_id: int,
    include_teams: bool = Query(False, description="Include teams in response")
):
    # Only load teams if requested
```

## Testing Complex Schemas

### Unit Test Example

```python
import pytest
from src.matches.schemas import MatchWithDetailsSchema

def test_match_with_details_schema_validation():
    """Test that MatchWithDetailsSchema validates correctly."""
    data = {
        "id": 1,
        "match_date": "2024-01-15T15:00:00",
        "week": 1,
        "team_a": {
            "id": 1,
            "title": "Team A",
            "city": "City A"
        },
        "team_b": {
            "id": 2,
            "title": "Team B",
            "city": "City B"
        },
        "tournament": {
            "id": 1,
            "title": "Tournament"
        }
    }

    schema = MatchWithDetailsSchema.model_validate(data)

    assert schema.id == 1
    assert schema.team_a.title == "Team A"
    assert schema.team_b.title == "Team B"
    assert schema.tournament.title == "Tournament"

def test_match_with_details_schema_optional_fields():
    """Test that optional nested fields can be None."""
    data = {
        "id": 1,
        "match_date": "2024-01-15T15:00:00",
        "week": 1,
        "team_a": None,
        "team_b": None,
        "tournament": None
    }

    schema = MatchWithDetailsSchema.model_validate(data)

    assert schema.team_a is None
    assert schema.team_b is None
    assert schema.tournament is None
```

### Integration Test Example

```python
@pytest.mark.asyncio
async def test_get_match_with_details_endpoint(async_client, test_match, test_team, test_tournament):
    """Test the /with-details/ endpoint returns proper nested data."""
    response = await async_client.get(f"/api/matches/{test_match.id}/with-details/")

    assert response.status_code == 200

    data = response.json()
    assert "id" in data
    assert "team_a" in data
    assert "team_b" in data
    assert "tournament" in data

    assert data["team_a"]["id"] == test_team.id
    assert data["team_a"]["title"] == test_team.title
    assert data["tournament"]["id"] == test_tournament.id
```

## Common Patterns

### Pattern 1: Read-Only Derived Schemas

Create combined schemas that inherit from base schemas:

```python
class MatchSchema(MatchSchemaCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

# Combined schema extends base with nested fields
class MatchWithDetailsSchema(MatchSchema):
    team_a: TeamSchema | None = None
    team_b: TeamSchema | None = None
    tournament: TournamentSchema | None = None
```

### Pattern 2: Multiple Detail Levels

Create schemas for different nesting depths:

```python
# Level 1: Direct relationships only
class MatchWithBasicDetailsSchema(MatchSchema):
    team_a: TeamSchema | None = None
    team_b: TeamSchema | None = None

# Level 2: Direct + one level of nested
class MatchWithExtendedDetailsSchema(MatchWithBasicDetailsSchema):
    tournament: TournamentSchema | None = None

# Level 3: Full nesting
class MatchWithFullDetailsSchema(MatchWithExtendedDetailsSchema):
    team_a_sport: SportSchema | None = None
    team_b_sport: SportSchema | None = None
```

### Pattern 3: Conditional Fields

Use query parameters to control what's included:

```python
@router.get("/matches/{id}/")
async def get_match_endpoint(
    match_id: int,
    include_teams: bool = Query(False),
    include_tournament: bool = Query(False),
    include_sponsors: bool = Query(False),
):
    # Build eager loading options based on params
    options = []
    if include_teams:
        options.extend([
            joinedload(MatchDB.team_a),
            joinedload(MatchDB.team_b),
        ])
    if include_tournament:
        options.append(joinedload(MatchDB.tournaments))
    if include_sponsors:
        options.extend([
            joinedload(MatchDB.main_sponsor),
            joinedload(MatchDB.sponsor_line),
        ])

    stmt = select(MatchDB).options(*options)
    # ... rest of implementation
```

## Troubleshooting

### Issue: Circular Import Error

**Error:** `ImportError: cannot import name 'Schema' from partially initialized module`

**Solution:** Use `TYPE_CHECKING` and string annotations:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.other.schemas import OtherSchema

class MySchema(BaseModel):
    related: "OtherSchema" | None = None
```

### Issue: N+1 Queries Still Happening

**Symptom:** Query logs show many similar queries

**Solution:** Ensure you're using eager loading in the service layer:

```python
# Check that options are applied
stmt = select(TeamDB).options(joinedload(TeamDB.sport))
```

### Issue: Response Too Slow

**Symptom:** Combined schema endpoint is slow

**Solutions:**
1. Add database indexes on FK columns
2. Limit nested collections (use pagination)
3. Profile the query with `EXPLAIN ANALYZE`
4. Consider separate endpoints for nested data
5. Use response caching for frequently accessed data

### Issue: Pydantic Validation Error

**Error:** `validation error for MatchWithDetailsSchema`

**Solutions:**
1. Check that `from_attributes=True` is set in `model_config`
2. Verify SQLAlchemy model relationships are correctly defined
3. Ensure eager loading is applied before `model_validate()`
4. Check for missing required fields in nested schemas

## Related Documentation

- [DEVELOPMENT_GUIDELINES.md](DEVELOPMENT_GUIDELINES.md) - General development patterns
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Full API reference
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
