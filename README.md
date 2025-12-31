# StatsBoards Backend

A FastAPI-based backend service for sports statistics and scoreboarding, designed to manage football (soccer) tournaments, matches, teams, and real-time game data.

## Features

- **Real-time Updates**: WebSocket support for live match data, scoreboards, and game clocks
- **Comprehensive Data Management**: Teams, players, tournaments, seasons, and match statistics
- **RESTful API**: Well-structured API endpoints following OpenAPI specifications
- **Database Integration**: PostgreSQL with async SQLAlchemy ORM
- **External Data Integration**: EESL system integration for data synchronization
- **File Management**: Secure file upload and static file serving
 - **Production Ready**: Docker deployment with nginx reverse proxy and SSL support
 - **Robust Error Handling**: Structured exception hierarchy and global error handlers
 - **Comprehensive Logging**: Standardized logging levels across all services
 - **Service Registry Pattern**: Dependency injection for decoupled service architecture

## Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL with asyncpg
- **ORM**: SQLAlchemy 2.0 (async)
- **Real-time**: WebSockets, Redis pub/sub
- **Testing**: pytest with pytest-asyncio
- **Deployment**: Docker, Gunicorn, Nginx
- **Code Quality**: Black, PyLint

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL
- Docker and Docker Compose (for testing and deployment)

### Installation

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd statsboards-backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**
   ```bash
   # Apply database migrations
   alembic upgrade head
   ```

6. **Run development server**
   ```bash
   python src/runserver.py
   ```

The API will be available at `http://localhost:9000`

## API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:9000/docs`
- **ReDoc**: `http://localhost:9000/redoc`

## Development

### Running Tests

```bash
# Start test database (required before running tests)
docker-compose -f docker-compose.test-db-only.yml up -d

# Run all tests
pytest

# Run tests for specific directory
pytest tests/test_db_services/
pytest tests/test_views/

# Run a single test file
pytest tests/test_db_services/test_tournament_service.py

# Run a specific test function
pytest tests/test_db_services/test_tournament_service.py::TestTournamentServiceDB::test_create_tournament_with_relations

# Run tests with coverage
pytest --cov=src

# Run tests with live logs enabled (for debugging)
pytest tests/test_db_services/test_tournament_service.py::TestTournamentServiceDB::test_create_tournament_with_relations -o log_cli=true
```

**Important:**
- Test database must be started before running tests: `docker-compose -f docker-compose.test-db-only.yml up -d`
- Tests use PostgreSQL (not SQLite) to ensure production compatibility
- The `pytest.ini` file includes performance optimizations: `-x -v --tb=short`
- Database echo is disabled in test fixtures for faster execution

### Code Quality

```bash
# Format code with Black
black src/ tests/

# Lint with PyLint
pylint src/
```

**Note:** After making code changes, run both formatting and linting commands to ensure code quality standards are met.

### Database Migrations

```bash
# Create new migration
poetry run alembic revision --autogenerate -m "Add new feature"

# Apply migrations
poetry run alembic upgrade head

# Check current version
poetry run alembic current
```

## Docker Deployment

### Development

```bash
docker-compose -f docker-compose.dev.yml up --build
```

### Production

```bash
docker-compose -f docker-compose.prod.yml up --build
```

### Testing

```bash
# Start test database only
docker-compose -f docker-compose.test-db-only.yml up -d

# Run tests against test database
pytest

# Stop test database
docker-compose -f docker-compose.test-db-only.yml down
```

### Database Testing

```bash
# Full test environment with database in container
docker-compose -f docker-compose.test.yml up --build
```

## Project Structure

```
src/
├── core/                        # Core application components
│   ├── config.py               # Configuration management
│   ├── models/                 # SQLAlchemy database models and mixins
│   │   ├── mixins/            # CRUD, query, and relationship mixins
│   │   └── [model files]     # Database model definitions
│   ├── exceptions.py          # Custom exception hierarchy
│   ├── exception_handler.py    # Global exception handlers
│   ├── base_router.py         # Base FastAPI router classes
│   ├── service_registry.py    # Service registry for dependency injection
│   └── service_initialization.py  # Service registration
├── teams/                      # Team management
│   ├── db_services.py         # Team service layer
│   ├── schemas.py            # Pydantic schemas
│   └── views.py              # API endpoints
├── matches/                    # Match management and scheduling
├── players/                    # Player data and statistics
├── tournaments/                # Tournament organization
├── seasons/                    # Season management
├── scoreboards/                # Scoreboard management
├── gameclocks/                 # Game clock functionality
├── playclocks/                 # Play clock functionality
├── matchdata/                  # Real-time match data
├── football_events/            # Game event tracking
├── sponsors/                   # Sponsor management
├── helpers/                    # Utility functions
│   ├── file_service.py        # File upload/download
│   ├── image_processing_service.py
│   └── upload_service.py
├── pars_eesl/                  # EESL data integration
├── utils/                      # WebSocket handlers
├── logging_config.py           # Logging configuration
├── main.py                     # FastAPI application entry point
├── runserver.py                # Development server
└── run_prod_server.py          # Production server
tests/                          # Test suite
├── test_db_services/          # Service layer tests
├── test_views/                # API endpoint tests
└── [test files]
AGENTS.md                       # Development guidelines for AI assistants
```

## Key Features

### Real-time Capabilities
- Live match data streaming via WebSockets
- Real-time scoreboard updates
- Game clock and play clock synchronization with background tasks
- Event notifications for football events
- Match data queue management for concurrent updates

### Data Management
- Complex many-to-many relationships (teams-tournaments, players-teams)
- Player statistics tracking across matches and tournaments
- Tournament and season management
- Sponsor and advertisement management with logo uploads
- Position and sport management
- Match data with detailed event tracking

### Error Handling & Logging
- Structured custom exception hierarchy
- Global exception handlers with appropriate HTTP status codes
- Standardized logging levels across all services
- Detailed error messages for debugging
- Proper exception chaining with stack traces

### External Integration
- EESL system data parsing and synchronization
- Automated data import/export capabilities
- Tournament team and player data parsing
- Match data parsing from external sources

### Code Quality
- Consistent service layer pattern with `BaseServiceDB`
- Service registry pattern for dependency injection and decoupling
- Comprehensive test coverage (500+ tests)
- Type hints throughout codebase
- Async/await for all database operations
- Mixin-based CRUD, query, and relationship operations

## API Endpoints

The API provides comprehensive endpoints for:

- **Sports**: `GET /api/sports/`, `POST /api/sports/`, `PUT /api/sports/{id}/`, `DELETE /api/sports/{id}/`
- **Seasons**: `GET /api/seasons/`, `POST /api/seasons/`, `PUT /api/seasons/{id}/`, `DELETE /api/seasons/{id}/`
- **Tournaments**: `GET /api/tournaments/`, `POST /api/tournaments/`, `PUT /api/tournaments/{id}/`, `DELETE /api/tournaments/{id}/`
- **Teams**: `GET /api/teams/`, `POST /api/teams/`, `PUT /api/teams/{id}/`, `DELETE /api/teams/{id}/`
- **Players**: `GET /api/players/`, `POST /api/players/`, `PUT /api/players/{id}/`, `DELETE /api/players/{id}/`
- **Matches**: `GET /api/matches/`, `POST /api/matches/`, `PUT /api/matches/{id}/`, `DELETE /api/matches/{id}/`
- **Scoreboards**: `GET /api/scoreboards/`, `POST /api/scoreboards/`, `PUT /api/scoreboards/{id}/`, `DELETE /api/scoreboards/{id}/`
- **Sponsors**: `GET /api/sponsors/`, `POST /api/sponsors/`, `PUT /api/sponsors/{id}/`, `DELETE /api/sponsors/{id}/`
- **Positions**: `GET /api/positions/`, `POST /api/positions/`, `PUT /api/positions/{id}/`, `DELETE /api/positions/{id}/`
- **Gameclocks**: `GET /api/gameclocks/`, `POST /api/gameclocks/`, `PUT /api/gameclocks/{id}/`
- **Playclocks**: `GET /api/playclocks/`, `POST /api/playclocks/`, `PUT /api/playclocks/{id}/`
- **Football Events**: `GET /api/football_events/`, `POST /api/football_events/`, `PUT /api/football_events/{id}/`

Each domain module follows the standard CRUD pattern with additional custom endpoints as needed.

## WebSocket Endpoints

- **Match Data**: `ws://localhost:9000/ws/matchdata/{match_id}`
- **Scoreboard**: `ws://localhost:9000/ws/scoreboard/{scoreboard_id}`

## Development Guidelines

The project uses `AGENTS.md` as a comprehensive development guide for AI assistants and developers. Key guidelines include:

### Code Style
- Follow existing patterns rather than creating new ones
- Use Python 3.11+ type hint syntax: `str | None` instead of `Optional[str]`
- Always annotate function parameters and return types
- Use Pydantic `Annotated` for field validation
- Keep functions focused and single-responsibility

### Exception Handling
- Use specific exception types instead of generic `except Exception:`
- Import custom exceptions from `src.core.exceptions`
- Follow the established exception handling pattern with proper logging levels
- Log with `exc_info=True` for stack traces

### Logging Standards
- **debug**: Detailed operation tracking
- **info**: Significant operations (creates, updates)
- **warning**: Expected but noteworthy situations (validation errors)
- **error**: Unexpected errors (database errors)
- **critical**: Unexpected exceptions that should rarely trigger

### Service Layer Pattern
- All service classes inherit from `BaseServiceDB`
- Use service registry for cross-service dependencies (never import other services directly)
- Access dependencies via `self.service_registry.get("service_name")`
- Registry uses lazy initialization to avoid circular dependencies
- Use async/await for all database operations
- Return database model objects, not dictionaries
- Use structured logging with consistent format

### Testing Requirements
- Tests must use PostgreSQL (not SQLite)
- Write descriptive docstrings for test methods
- Test both success and error paths
- Use factory classes from `tests/factories.py`

For complete development guidelines, see `AGENTS.md`.

## Configuration

### Environment Variables

Key environment variables (see `.env.example`):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ALLOWED_ORIGINS`: CORS allowed origins
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Logging

Logging is configured via YAML files (`logging-config_dev.yaml`, `logging-config_info.yaml`). Call `setup_logging()` at module level in services and routers.

**Log Levels:**
- **debug**: Detailed operation tracking
- **info**: Significant operations (creates, updates)
- **warning**: Expected but noteworthy situations (validation errors)
- **error**: Unexpected errors (database errors)
- **critical**: Unexpected errors that should rarely trigger

**Log Format:**
- Structured logging with consistent format across all services
- Logs written to console and log files in `logs/` directory
- Use `exc_info=True` for exception logging to capture stack traces

## Contributing

1. Fork repository
2. Create a feature branch
3. Make your changes following the guidelines in `AGENTS.md`
4. Add tests for new functionality
5. Run tests: `docker-compose -f docker-compose.test-db-only.yml up -d && pytest`
6. Format code: `black src/ tests/`
7. Lint code: `pylint src/`
8. Ensure all tests pass
9. Submit a pull request

**Important:**
- All commits must be by linroot with email nevalions@gmail.com
- Follow the existing code patterns and conventions
- Read `AGENTS.md` for comprehensive development guidelines

## Recent Improvements

### Exception Handling Refactoring
- Replaced generic `except Exception` clauses with specific exception types across all services
- Implemented custom exception hierarchy in `src/core/exceptions.py`
- Added global exception handlers with appropriate HTTP status codes
- Improved error detection and debugging capabilities
- Enhanced logging with appropriate levels for each exception type

### Logging Standardization
- Established clear logging guidelines with consistent levels
- Updated all database services to use appropriate log levels
- Changed successful operations from debug to info
- Changed validation/schema errors from error to warning
- Maintained error level for database failures
- Maintained critical level for unexpected errors

### Performance Optimizations
- Optimized match data fetching with parallel database calls
- Transaction rollback per test for faster execution
- Database echo disabled in test fixtures
- Session-scoped database engine for tests
- Improved query performance in service layer

### Testing Improvements
- 527+ comprehensive tests passing
- Test database optimization with Docker
- PostgreSQL requirement for tests (not SQLite)
- Factory pattern for test data generation
- Comprehensive test coverage across all services

### Service Layer Decoupling
- Implemented service registry pattern for dependency injection
- Services no longer directly import or instantiate other services
- Centralized service registration in `src/core/service_initialization.py`
- Lazy initialization to avoid circular dependencies
- Improved testability through dependency injection
- See `SERVICE_LAYER_DECOUPLING.md` for complete documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the repository or contact the development team.
