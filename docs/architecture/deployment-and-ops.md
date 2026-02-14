# Deployment and Ops

## Error Handling

- Domain exceptions in `src/core/exceptions.py`
- Global handlers in `src/core/exception_handler.py`
- Use `handle_service_exceptions` and `handle_view_exceptions`

## Configuration Management

- Pydantic settings in `src/core/config.py`
- Validation via `validate_config.py`
- See `docs/CONFIGURATION_VALIDATION.md`

## Testing Architecture

- Pytest with xdist (8 workers)
- Transaction rollback per test
- Dedicated test DBs for each worker

## Performance

- Async DB I/O and connection pooling
- Cache for match data to reduce reads
- WebSockets avoid per-second DB writes

## Deployment

- Dev: `python -m src.runserver`
- Prod: `python -m src.run_prod_server`
- Docker compose for DB and app services

## Security Considerations

- Input validation with Pydantic
- Role-based access with `require_roles`
- File upload validation and safe paths
