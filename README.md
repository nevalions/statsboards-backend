# StatsBoards Backend

A FastAPI-based backend service for sports statistics and scoreboarding, designed to manage football (soccer) tournaments, matches, teams, players, and real-time game data.

## Features

- **Real-time Updates**: WebSocket support for live match data, scoreboards, and game clocks
- **Comprehensive Data Management**: Teams, players, tournaments, seasons, and match statistics
- **RESTful API**: Well-structured API endpoints following OpenAPI specifications
- **Database Integration**: PostgreSQL with async SQLAlchemy ORM
- **External Data Integration**: EESL system integration for data synchronization
- **File Management**: Secure file upload and static file serving
- **Production Ready**: Docker deployment with nginx reverse proxy and SSL support

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
- Redis (optional, for development)
- Docker and Docker Compose (for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd statsboards-backend
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up database**
   ```bash
   # Apply database migrations
   poetry run alembic upgrade head
   ```

5. **Run the development server**
   ```bash
   poetry run python src/runserver.py
   ```

The API will be available at `http://localhost:9000`

## API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:9000/docs`
- **ReDoc**: `http://localhost:9000/redoc`

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src

# Run specific test file
poetry run pytest tests/test_example.py
```

### Code Quality

```bash
# Format code
poetry run black src/ tests/

# Lint code
poetry run pylint src/
```

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

## Project Structure

```
src/
├── core/                   # Core application components
│   ├── config.py          # Configuration management
│   ├── models/            # SQLAlchemy database models
│   └── base_router.py     # Base FastAPI router classes
├── teams/                 # Team management
├── matches/               # Match management and scheduling
├── players/               # Player data and statistics
├── tournaments/           # Tournament organization
├── seasons/               # Season management
├── scoreboards/           # Scoreboard management
├── gameclocks/            # Game clock functionality
├── matchdata/             # Real-time match data
├── football_events/       # Game event tracking
├── sponsors/              # Sponsor management
├── helpers/               # Utility functions
├── pars_eesl/             # EESL data integration
├── main.py                # FastAPI application entry point
├── runserver.py           # Development server
└── run_prod_server.py     # Production server
```

## Key Features

### Real-time Capabilities
- Live match data streaming via WebSockets
- Real-time scoreboard updates
- Game clock and play clock synchronization
- Event notifications for football events

### Data Management
- Complex many-to-many relationships (teams-tournaments, players-teams)
- Player statistics tracking
- Tournament and season management
- Sponsor and advertisement management

### External Integration
- EESL system data parsing and synchronization
- Automated data import/export capabilities
- External API integration support

## API Endpoints

The API provides comprehensive endpoints for:

- **Sports**: `GET /api/sports/`
- **Seasons**: `GET /api/seasons/`
- **Tournaments**: `GET /api/tournaments/`
- **Teams**: `GET /api/teams/`
- **Players**: `GET /api/players/`
- **Matches**: `GET /api/matches/`
- **Scoreboards**: `GET /api/scoreboards/`
- **Sponsors**: `GET /api/sponsors/`

## WebSocket Endpoints

- **Match Data**: `ws://localhost:9000/ws/matchdata/{match_id}`
- **Scoreboard**: `ws://localhost:9000/ws/scoreboard/{scoreboard_id}`

## Configuration

### Environment Variables

Key environment variables (see `.env.example`):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ALLOWED_ORIGINS`: CORS allowed origins
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Logging

Logging is configured via YAML files in `src/logging_config.py`. Logs are written to:
- Console output
- Log files in `logs/` directory
- Structured logging with correlation IDs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the repository or contact the development team.
