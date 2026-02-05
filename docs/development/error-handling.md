# Error Handling

Avoid generic `except Exception:` clauses. Use specific exception types for better debugging and error monitoring.

Custom exceptions from `src.core.exceptions`:

- `ValidationError`
- `NotFoundError`
- `DatabaseError`
- `BusinessLogicError`
- `ExternalServiceError`
- `ConfigurationError`
- `AuthenticationError`
- `AuthorizationError`
- `ConcurrencyError`
- `FileOperationError`
- `ParsingError`

## Service Layer Decorator

Prefer `@handle_service_exceptions`:

```python
from src.core.models import handle_service_exceptions

@handle_service_exceptions(item_name=ITEM, operation="creating")
async def create(self, item: TeamSchemaCreate) -> TeamDB:
    team = self.model(**item.model_dump())
    return await super().create(team)

@handle_service_exceptions(
    item_name=ITEM,
    operation="fetching players",
    return_value_on_not_found=[],
)
async def get_players_by_team_id(self, team_id: int) -> list[PlayerDB]:
    async with self.db.get_session_maker()() as session:
        stmt = select(PlayerDB).where(PlayerDB.team_id == team_id)
        results = await session.execute(stmt)
        return results.scalars().all()

@handle_service_exceptions(
    item_name=ITEM,
    operation="fetching by ID",
    reraise_not_found=True,
)
async def get_by_id(self, item_id: int) -> TeamDB:
    return await super().get_by_id(item_id)
```

## View Layer Decorator

Use `@handle_view_exceptions` for FastAPI routers:

```python
from src.core.models import handle_view_exceptions

@router.post("/upload_logo", response_model=UploadTeamLogoResponse)
@handle_view_exceptions(
    error_message="Error uploading team logo",
    status_code=500,
)
async def upload_team_logo_endpoint(file: UploadFile = File(...)):
    file_location = await file_service.save_upload_image(file, sub_folder="teams/logos")
    return {"logoUrl": file_location}
```

The decorator:

- Re-raises `HTTPException` unchanged
- Converts other exceptions to `HTTPException`
- Logs with error level
- Uses `self.logger` when available

## Manual try/except Order

Use manual blocks only when needed for custom cleanup or behavior:

```python
try:
    ...
except HTTPException:
    raise
except (IntegrityError, SQLAlchemyError) as ex:
    self.logger.error(f"Database error: {ex}", exc_info=True)
    raise HTTPException(status_code=500, detail="Database error") from ex
except ValidationError as ex:
    self.logger.warning(f"Validation error: {ex}", exc_info=True)
    raise HTTPException(status_code=400, detail=str(ex)) from ex
except (ValueError, KeyError, TypeError) as ex:
    self.logger.warning(f"Data error: {ex}", exc_info=True)
    raise HTTPException(status_code=400, detail="Invalid data") from ex
except NotFoundError as ex:
    self.logger.info(f"Not found: {ex}", exc_info=True)
    raise HTTPException(status_code=404, detail=str(ex)) from ex
except BusinessLogicError as ex:
    self.logger.error(f"Business logic error: {ex}", exc_info=True)
    raise HTTPException(status_code=422, detail=str(ex)) from ex
except Exception as ex:
    self.logger.critical(f"Unexpected error: {ex}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error") from ex
```

## Status Code Guidance

- 400: ValidationError, ValueError, KeyError, TypeError
- 401: AuthenticationError
- 403: AuthorizationError
- 404: NotFoundError
- 409: IntegrityError, ConcurrencyError
- 422: BusinessLogicError
- 500: DatabaseError, unexpected errors
- 503: ExternalServiceError, ConnectionError
- 504: TimeoutError
