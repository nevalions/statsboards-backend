# Refactoring Plan: Generic Exception Catching

## Executive Summary

**Goal**: Replace broad `except Exception` clauses with specific exception handling to improve error detection, debugging, and monitoring while maintaining current safety and logging.

**Impact**: ~153 exception handling blocks across `db_services.py` and `views.py` files.

**Priority**: Medium (not critical but improves maintainability and debugging)

---

## Current State Analysis

### Statistics
- **Total files affected**: 32 files
- **db_services.py files**: 82 generic exception catches
- **views.py files**: 71 generic exception catches
- **Total instances**: 153

### Current Pattern (Prevalent)
```python
try:
    # business logic
except HTTPException:
    raise
except (IntegrityError, SQLAlchemyError) as ex:
    self.logger.error(f"Database error: {ex}", exc_info=True)
    raise HTTPException(status_code=500, detail="Database error...")
except Exception as ex:  # PROBLEM: Too broad
    self.logger.error(f"Error: {ex}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error...")
```

### Issues Identified
1. **Obscures error types** - Catches `KeyError`, `AttributeError`, `TypeError`, `ValueError` equally
2. **Hides programming errors** - Bugs treated as "internal server errors"
3. **Debugging difficulty** - Cannot distinguish expected vs. unexpected errors
4. **Alerting challenges** - Cannot monitor specific error types differently
5. **Inconsistent handling** - Different errors get same 500 status

### What's Working Well (Keep This)
- ✅ Exception chaining with `exc_info=True` for stack traces
- ✅ Multiple specific catches before generic one
- ✅ HTTPException conversion prevents information leakage
- ✅ Comprehensive logging
- ✅ Proper error messages returned to clients

---

## Proposed Architecture

### 1. Custom Exception Hierarchy

Create a structured exception system in `src/core/exceptions.py`:

```python
# Core exception classes
class StatsBoardException(Exception):
    """Base exception for all application-specific errors"""
    pass

class DatabaseError(StatsBoardException):
    """Database-related errors"""
    pass

class ValidationError(StatsBoardException):
    """Data validation errors"""
    pass

class NotFoundError(StatsBoardException):
    """Resource not found errors"""
    pass

class BusinessLogicError(StatsBoardException):
    """Business rule violations"""
    pass

class ExternalServiceError(StatsBoardException):
    """External service integration errors"""
    pass
```

### 2. Standard Exception Groups

Define Python built-in exceptions that should be caught specifically:

| Exception Group | Examples | HTTP Status |
|----------------|----------|-------------|
| **ValueError** | Invalid data format, conversion errors | 400 Bad Request |
| **KeyError** | Missing required keys | 400 Bad Request |
| **AttributeError** | Invalid attribute access | 500 Internal Error |
| **TypeError** | Type mismatches | 400 Bad Request |
| **RuntimeError** | General runtime issues | 500 Internal Error |
| **ConnectionError** | Network/connection issues | 503 Service Unavailable |
| **TimeoutError** | Operation timeout | 504 Gateway Timeout |

### 3. Global Exception Handler Middleware

Create `src/core/exception_handler.py`:

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

# Map exceptions to HTTP status codes
EXCEPTION_MAPPING = {
    ValueError: (status.HTTP_400_BAD_REQUEST, "Bad Request"),
    KeyError: (status.HTTP_400_BAD_REQUEST, "Bad Request"),
    TypeError: (status.HTTP_400_BAD_REQUEST, "Bad Request"),
    ValidationError: (status.HTTP_400_BAD_REQUEST, "Validation Error"),
    NotFoundError: (status.HTTP_404_NOT_FOUND, "Not Found"),
    IntegrityError: (status.HTTP_409_CONFLICT, "Conflict"),
    SQLAlchemyError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Database Error"),
    ConnectionError: (status.HTTP_503_SERVICE_UNAVAILABLE, "Service Unavailable"),
    TimeoutError: (status.HTTP_504_GATEWAY_TIMEOUT, "Gateway Timeout"),
}

def register_exception_handlers(app: FastAPI):
    """Register global exception handlers"""
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # This should only catch truly unexpected errors
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "type": type(exc).__name__,
            }
        )
```

### 4. Refactored Exception Handling Pattern

**New Pattern (Recommended):**
```python
try:
    # business logic
except HTTPException:
    raise
except (IntegrityError, SQLAlchemyError) as ex:
    self.logger.error(f"Database error: {ex}", exc_info=True)
    raise HTTPException(status_code=500, detail="Database error...")
except ValidationError as ex:
    self.logger.warning(f"Validation error: {ex}", exc_info=True)
    raise HTTPException(status_code=400, detail=str(ex))
except (ValueError, KeyError, TypeError) as ex:
    self.logger.warning(f"Data error: {ex}", exc_info=True)
    raise HTTPException(status_code=400, detail="Invalid data provided")
except NotFoundError as ex:
    self.logger.info(f"Resource not found: {ex}", exc_info=True)
    raise HTTPException(status_code=404, detail=str(ex))
except BusinessLogicError as ex:
    self.logger.error(f"Business logic error: {ex}", exc_info=True)
    raise HTTPException(status_code=422, detail=str(ex))
except ConnectionError as ex:
    self.logger.error(f"Connection error: {ex}", exc_info=True)
    raise HTTPException(status_code=503, detail="Service unavailable")
except Exception as ex:
    # Only for truly unexpected errors - should rarely trigger
    self.logger.critical(
        f"Unexpected error in {self.__class__.__name__}: {ex}",
        exc_info=True
    )
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Migration Strategy

### Phase 1: Foundation (1-2 days)

**Tasks:**
1. Create `src/core/exceptions.py` with custom exception hierarchy
2. Create `src/core/exception_handler.py` with global handler
3. Register global handlers in `src/main.py`
4. Write unit tests for new exception classes
5. Update documentation in AGENTS.md

**Files to Create/Modify:**
- ✨ `src/core/exceptions.py` (new)
- ✨ `src/core/exception_handler.py` (new)
- 📝 `src/main.py` (add handler registration)
- 📝 `AGENTS.md` (add exception handling guidelines)

### Phase 2: Mixin Layer (2-3 days)

**Tasks:**
1. Refactor `src/core/models/mixins/crud_mixin.py`
2. Refactor `src/core/models/mixins/query_mixin.py`
3. Refactor `src/core/models/mixins/relationship_mixin.py`
4. Add comprehensive logging for each exception type
5. Add tests for refactored mixins

**Priority: HIGH** - Mixins are used by all services

**Files to Modify:**
- 📝 `src/core/models/mixins/crud_mixin.py` (4 generic catches)
- 📝 `src/core/models/mixins/query_mixin.py` (2 generic catches)
- 📝 `src/core/models/mixins/relationship_mixin.py` (2 generic catches)

### Phase 3: Database Services (5-7 days)

**Tasks:**
Group services by complexity and dependencies:

#### Group 1: Simple Services (1 day)
- `src/sponsors/db_services.py` (1)
- `src/sponsor_lines/db_services.py` (1)
- `src/person/db_services.py` (1)
- `src/player/db_services.py` (2)
- `src/sports/db_services.py` (2)

#### Group 2: Medium Complexity (2 days)
- `src/teams/db_services.py` (3)
- `src/positions/db_services.py` (2)
- `src/seasons/db_services.py` (5)
- `src/tournaments/db_services.py` (2)
- `src/gameclocks/db_services.py` (1)

#### Group 3: High Complexity (2-3 days)
- `src/player_team_tournament/db_services.py` (6)
- `src/player_match/db_services.py` (9)
- `src/matches/db_services.py` (7)
- `src/scoreboards/db_services.py` (3)
- `src/playclocks/db_services.py` (3)
- `src/team_tournament/db_services.py` (3)
- `src/sponsor_sponsor_line_connection/db_services.py` (4)

### Phase 4: API Views/Routers (5-7 days)

**Tasks:**
Same grouping as Phase 3:

#### Group 1: Simple Views (1 day)
- `src/sponsors/views.py` (1)
- `src/sponsor_lines/views.py` (3)
- `src/matches/views.py` (0) - ✅ Already good!
- `src/teams/views.py` (9)
- `src/team_tournament/views.py` (0) - ✅ Already good!
- `src/sports/views.py` (0) - ✅ Already good!

#### Group 2: Medium Complexity (2 days)
- `src/person/views.py` (3)
- `src/player/views.py` (3)
- `src/positions/views.py` (3)
- `src/tournaments/views.py` (3)
- `src/football_events/views.py` (3)
- `src/gameclocks/views.py` (5)

#### Group 3: High Complexity (2-3 days)
- `src/player_team_tournament/views.py` (5)
- `src/player_match/views.py` (5)
- `src/matchdata/views.py` (8)
- `src/scoreboards/views.py` (2)
- `src/playclocks/views.py` (5)
- `src/sponsor_sponsor_line_connection/views.py` (5)
- `src/seasons/views.py` (4)

### Phase 5: Testing & Validation (2-3 days)

**Tasks:**
1. Run full test suite: `pytest`
2. Run linting: `pylint src/`
3. Integration testing with test database
4. Error injection testing
5. Performance impact testing
6. Log analysis verification

### Phase 6: Documentation & Monitoring (1 day)

**Tasks:**
1. Update AGENTS.md with new patterns
2. Create exception handling documentation
3. Configure alerting for specific error types
4. Create migration guide for developers

---

## Implementation Examples

### Example 1: CRUDMixin.get_by_id()

**Before:**
```python
async def get_by_id(self, item_id: int):
    try:
        async with self.db.async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == item_id)
            )
            # ... logic ...
    except Exception as ex:
        self.logger.error(f"Error fetching element: {ex}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch element")
```

**After:**
```python
async def get_by_id(self, item_id: int):
    try:
        async with self.db.async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == item_id)
            )
            # ... logic ...
    except HTTPException:
        raise
    except (IntegrityError, SQLAlchemyError) as ex:
        self.logger.error(f"Database error fetching element {item_id}: {ex}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error fetching {self.model.__name__}")
    except Exception as ex:
        # Truly unexpected - should rarely trigger
        self.logger.critical(
            f"Unexpected error in {self.__class__.__name__}.get_by_id({item_id}): {ex}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Example 2: TeamServiceDB.create()

**Before:**
```python
async def create(self, item: TeamSchemaCreate | TeamSchemaUpdate) -> TeamDB:
    try:
        team = self.model(...)
        return await super().create(team)
    except Exception as ex:
        self.logger.error(f"Error creating TEAM {ex}", exc_info=True)
        raise HTTPException(status_code=409, detail="Error creating team")
```

**After:**
```python
async def create(self, item: TeamSchemaCreate | TeamSchemaUpdate) -> TeamDB:
    try:
        team = self.model(...)
        return await super().create(team)
    except HTTPException:
        raise
    except (IntegrityError, SQLAlchemyError) as ex:
        self.logger.error(f"Database error creating team: {ex}", exc_info=True)
        raise HTTPException(status_code=409, detail="Team already exists or database error")
    except (ValueError, TypeError) as ex:
        self.logger.warning(f"Invalid data creating team: {ex}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid team data: {str(ex)}")
    except Exception as ex:
        self.logger.critical(f"Unexpected error creating team: {ex}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Example 3: PlayerMatchServiceDB.create_or_update_player_match()

**Before:**
```python
async def create_or_update_player_match(self, p: PlayerMatchSchemaCreate) -> PlayerMatchDB | None:
    try:
        if p.player_match_eesl_id and p.match_id:
            player_match_from_db = await self.get_player_match_by_match_id_and_eesl_id(...)
            # ... logic ...
        else:
            return await self.create_new_player_match(p)
    except Exception as ex:
        self.logger.error(f"Error creating or updating PLAYER_MATCH: {ex}", exc_info=True)
        return None
```

**After:**
```python
async def create_or_update_player_match(self, p: PlayerMatchSchemaCreate) -> PlayerMatchDB | None:
    try:
        if p.player_match_eesl_id and p.match_id:
            player_match_from_db = await self.get_player_match_by_match_id_and_eesl_id(...)
            # ... logic ...
        else:
            return await self.create_new_player_match(p)
    except HTTPException:
        raise
    except (IntegrityError, SQLAlchemyError) as ex:
        self.logger.error(f"Database error in create_or_update_player_match: {ex}", exc_info=True)
        raise
    except (ValueError, KeyError) as ex:
        self.logger.warning(f"Invalid player match data: {ex}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid player match data")
    except Exception as ex:
        self.logger.critical(f"Unexpected error in create_or_update_player_match: {ex}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Risk Assessment

### High Risk Areas
1. **Mixins** - Changes affect all services
2. **High-complexity services** (player_match, matches) - More edge cases

### Mitigation Strategies
1. **Thorough testing** after each group completion
2. **Feature flags** if possible (not practical for this project)
3. **Incremental deployment** - Deploy changes in phases
4. **Rollback plan** - Keep branch for quick revert
5. **Monitoring** - Watch error rates closely after deployment

### Expected Benefits
- ✅ Better error detection and debugging
- ✅ More precise HTTP status codes
- ✅ Improved error monitoring/alerting
- ✅ Better client experience with specific error messages
- ✅ Reduced bug hiding

### Potential Drawbacks
- ⚠️ Initial refactoring effort (~15-20 days)
- ⚠️ Slightly more verbose code
- ⚠️ Need to add new exception types as needed
- ⚠️ Temporary risk of introducing bugs during refactoring

---

## Success Metrics

### Code Quality
- Reduce `except Exception` usage from 153 to < 20
- Increase code coverage to > 90% for exception handling
- Pass pylint without warnings

### Operational
- Reduce mean time to detection (MTTD) for bugs
- Improve error categorization in monitoring
- Maintain zero downtime during deployment

### Testing
- All existing tests pass
- New tests cover all exception paths
- Error injection tests pass

---

## Rollout Plan

### Week 1
- Days 1-2: Phase 1 (Foundation)
- Days 3-4: Phase 2 (Mixins)
- Days 5-7: Phase 3 (Group 1 services)

### Week 2
- Days 1-2: Phase 3 (Group 2 services)
- Days 3-4: Phase 3 (Group 3 services)
- Days 5-6: Phase 4 (Groups 1-2 views)

### Week 3
- Days 1-2: Phase 4 (Group 3 views)
- Days 3-5: Phase 5 (Testing & Validation)
- Day 6: Phase 6 (Documentation & Monitoring)

---

## Checklist for Each File

When refactoring each file, ensure:

- [ ] All existing tests pass
- [ ] New exception types imported
- [ ] Specific exceptions caught before generic
- [ ] Logging includes exception type
- [ ] HTTP status codes are appropriate
- [ ] Error messages are clear but not leaky
- [ ] No bare `except:` clauses
- [ ] `exc_info=True` for all logger.error/critical calls
- [ ] Code style matches AGENTS.md guidelines
- [ ] No new pylint warnings

---

## Conclusion

This refactoring plan provides a structured approach to improving exception handling while minimizing risk. The phased approach allows for incremental improvements and thorough testing at each stage.

**Estimated Effort**: 15-20 developer days
**Risk Level**: Medium (mitigated by phased approach and testing)
**Priority**: Medium (improves maintainability and debugging)

Proceed with Phase 1 when approved.
