# Exception Handling Refactor Summary

## Overview
Successfully implemented a decorator-based exception handling system to eliminate repetitive try/except boilerplate in service layer.

## Changes Made

### 1. Created `@handle_service_exceptions` Decorator
- Location: `src/core/models/base.py`
- Automatically handles all common exception types
- Reduces 10-15 lines of boilerplate per method to 1 decorator
- Supports both sync and async methods
- Configurable behavior via parameters:
  - `item_name`: Name of the item being operated on
  - `operation`: Description of the operation
  - `reraise_not_found`: Whether to raise HTTPException for NotFoundError
  - `return_value_on_not_found`: Value to return when NotFoundError is caught

### 2. Updated Service Files
Refactored methods in the following services to use the decorator:

#### `src/matches/db_services.py`
- `create()` - Creating match records
- `get_sport_by_match_id()` - Fetching sport by match ID
- `get_teams_by_match_id()` - Fetching teams by match ID
- `get_players_by_match()` - Fetching players by match ID
- `get_player_by_match_full_data()` - Fetching full player data by match ID
- `get_scoreboard_by_match()` - Fetching scoreboard by match ID
- `get_teams_by_match()` - Fetching teams (v2) by match ID

#### `src/teams/db_services.py`
- `create()` - Creating team records
- `get_players_by_team_id_tournament_id()` - Fetching players by team and tournament ID
- `get_players_by_team_id_tournament_id_with_person()` - Fetching players with person data

### 3. Updated Documentation
- Added decorator usage examples to `AGENTS.md`
- Updated error handling guidelines to prefer decorator pattern
- Documented manual try/except use cases

## Benefits

### Code Reduction
- **Before**: 10-15 lines of try/except boilerplate per method
- **After**: 1 decorator line
- **Savings**: ~9-14 lines per method

### Consistency
- All exception handling logic is centralized in one place
- Consistent error messages and logging across all services
- Consistent HTTP status codes for each error type

### Maintainability
- Change exception handling behavior in one location
- Easier to add new exception types globally
- Simpler to update error messages or logging format

### Readability
- Business logic is the focus, not error handling
- Methods are shorter and easier to understand
- Intent is clear from decorator parameters

## Usage Examples

### Creating Records (Raise on NotFoundError)
```python
@handle_service_exceptions(item_name=ITEM, operation="creating")
async def create(self, item: TeamSchemaCreate) -> TeamDB:
    team = self.model(**item.model_dump())
    return await super().create(team)
```

### Fetching Records (Return Empty on NotFoundError)
```python
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
```

### Fetching Records (Raise HTTPException on NotFoundError)
```python
@handle_service_exceptions(
    item_name=ITEM,
    operation="fetching by ID",
    reraise_not_found=True
)
async def get_by_id(self, item_id: int) -> TeamDB:
    return await super().get_by_id(item_id)
```

## Exception Handling Behavior

The decorator handles the following exception types in order:

1. **HTTPException**: Re-raises without modification
2. **IntegrityError, SQLAlchemyError**: Logs error, raises 500
3. **ValueError, KeyError, TypeError**: Logs warning, raises 400
4. **NotFoundError**: Logs info, either raises 404 or returns `return_value_on_not_found`
5. **BusinessLogicError**: Logs error, raises 422
6. **Exception**: Logs critical, raises 500

## Testing

All existing tests pass:
- `tests/test_db_services/test_match_service.py`: 5 tests passed
- `tests/test_db_services/test_team_service.py`: 6 tests passed
- `tests/test_db_services/`: 123 tests passed

## Future Work

To complete this refactoring, apply the decorator to all remaining service methods that use the boilerplate pattern. Priority services include:
- Player service
- Tournament service
- Person service
- Football event service
- And all other services with similar patterns

## Notes

- Type checking may show warnings for `create()` methods that use the decorator, as the decorator can theoretically return `None` even though `NotFoundError` won't be raised in practice. This is a known limitation of the decorator pattern and doesn't affect runtime behavior.
- Manual try/except blocks are still appropriate for special cases that require custom error handling logic.
