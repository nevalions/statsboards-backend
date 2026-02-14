# Essential Commands

## Prerequisites

Activate the virtual environment before running tools:

```bash
source venv/bin/activate
```

## Testing

Recommended fast run (restarts test DB, 8 workers):

```bash
./run-tests.sh
```

Other common test commands:

```bash
# Fast tests (parallel with 8 workers, skips slow/integration)
pytest

# All tests including slow/integration
pytest -m ""

# Only slow tests
pytest -m "slow"

# Sequential (debugging)
pytest -n 0

# Coverage
./run-tests.sh --cov=src --cov-report=html
```

Notes:

- `pytest.ini` defaults to `-n 8` and skips `slow` and `integration` tests.
- Use `@pytest.mark.timeout(N)` for tests that legitimately exceed the 30s default timeout.

## Test Markers

- `@pytest.mark.integration` - Hits external websites or production-like folders
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow tests (skipped by default)
- `@pytest.mark.property` - Property-based tests
- `@pytest.mark.timeout(N)` - Per-test timeout override

## Code Quality

```bash
ruff check src/ tests/
ruff check --fix src/ tests/
```

## Database

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

## Running the Application

```bash
python -m src.runserver
python -m src.run_prod_server
```

## Configuration Validation

```bash
python validate_config.py
```
