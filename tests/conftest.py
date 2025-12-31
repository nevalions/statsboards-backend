import os
import shutil

import pytest
import pytest_asyncio

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.core import settings
from src.core.models.base import Base, Database
from src.core.service_registry import init_service_registry
from src.core.service_initialization import register_all_services

db_url = settings.test_db.test_db_url

# Import fixtures from fixtures.py
pytest_plugins = ["tests.fixtures"]


# Custom markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks test as integration test (hits real website)"
    )
    config.addinivalue_line(
        "markers", "benchmark: marks test as performance benchmark"
    )
    config.addinivalue_line(
        "markers", "e2e: marks test as end-to-end integration test"
    )
    config.addinivalue_line(
        "markers", "slow: marks test as slow-running"
    )


# Database fixture that ensures a clean state using transactions, function-scoped
@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Database fixture that ensures a clean state using transactions."""
    db_url_str = str(db_url)
    assert "test" in db_url_str, "Test DB URL must contain 'test'"

    database = Database(db_url_str, echo=False)

    # Initialize service registry for each test
    init_service_registry(database)
    register_all_services(database)

    # Create tables at start of each test (faster than migrations)
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Use a transactional connection for tests
    async with database.engine.connect() as connection:
        transaction = await connection.begin()
        database.async_session.configure(bind=connection)

        try:
            yield database
            if transaction.is_active:
                await transaction.rollback()
        finally:
            # No need to drop tables - transaction rollback cleans up
            pass


@pytest.fixture(scope="session")
def test_downloads_dir():
    """Fixture to create and clean up test downloads directory."""
    downloads_dir = os.path.join(os.path.dirname(__file__), "test_downloads")

    # Create directory before tests
    os.makedirs(downloads_dir, exist_ok=True)

    yield downloads_dir

    # Clean up after all tests complete
    if os.path.exists(downloads_dir):
        shutil.rmtree(downloads_dir)
        print(f"\nCleaned up test downloads directory: {downloads_dir}")


@pytest.fixture
def test_uploads_path(test_downloads_dir, monkeypatch):
    """Fixture to patch uploads_path for integration tests."""
    # Patch the config module's uploads_path directly
    import src.core.config as config_module

    monkeypatch.setattr(config_module, "uploads_path", test_downloads_dir)
    return test_downloads_dir


@pytest_asyncio.fixture(scope="function")
async def test_app(test_db):
    """Create FastAPI test app with all routers."""
    from src.matches.views import api_match_crud_router, api_match_websocket_router, api_match_parser_router
    from src.football_events.views import FootballEventAPIRouter
    from src.football_events.db_services import FootballEventServiceDB
    from src.gameclocks.views import GameClockAPIRouter
    from src.gameclocks.db_services import GameClockServiceDB
    from src.matchdata.views import MatchDataAPIRouter
    from src.matchdata.db_services import MatchDataServiceDB
    from src.person.views import PersonAPIRouter
    from src.person.db_services import PersonServiceDB
    from src.playclocks.views import PlayClockAPIRouter
    from src.playclocks.db_services import PlayClockServiceDB
    from src.player.views import PlayerAPIRouter
    from src.player.db_services import PlayerServiceDB
    from src.player_match import api_player_match_router
    from src.player_team_tournament.views import PlayerTeamTournamentAPIRouter
    from src.player_team_tournament.db_services import PlayerTeamTournamentServiceDB
    from src.positions.views import PositionAPIRouter
    from src.positions.db_services import PositionServiceDB
    from src.scoreboards.views import ScoreboardAPIRouter
    from src.scoreboards.db_services import ScoreboardServiceDB
    from src.seasons.views import SeasonAPIRouter
    from src.seasons.db_services import SeasonServiceDB
    from src.sponsor_lines.views import SponsorLineAPIRouter
    from src.sponsor_lines.db_services import SponsorLineServiceDB
    from src.sponsor_sponsor_line_connection import api_sponsor_sponsor_line_router
    from src.sponsors.views import SponsorAPIRouter
    from src.sponsors.db_services import SponsorServiceDB
    from src.sports.views import SportAPIRouter
    from src.sports.db_services import SportServiceDB
    from src.team_tournament.views import TeamTournamentRouter
    from src.team_tournament.db_services import TeamTournamentServiceDB
    from src.teams.views import TeamAPIRouter
    from src.teams.db_services import TeamServiceDB
    from src.tournaments.views import TournamentAPIRouter
    from src.tournaments.db_services import TournamentServiceDB

    app = FastAPI()
    app.include_router(api_match_crud_router)
    app.include_router(api_match_websocket_router)
    app.include_router(api_match_parser_router)
    app.include_router(FootballEventAPIRouter(FootballEventServiceDB(test_db)).route())
    app.include_router(GameClockAPIRouter(GameClockServiceDB(test_db)).route())
    app.include_router(MatchDataAPIRouter(MatchDataServiceDB(test_db)).route())
    app.include_router(PersonAPIRouter(PersonServiceDB(test_db)).route())
    app.include_router(PlayClockAPIRouter(PlayClockServiceDB(test_db)).route())
    app.include_router(PlayerAPIRouter(PlayerServiceDB(test_db)).route())
    app.include_router(api_player_match_router)
    app.include_router(PlayerTeamTournamentAPIRouter(PlayerTeamTournamentServiceDB(test_db)).route())
    app.include_router(PositionAPIRouter(PositionServiceDB(test_db)).route())
    app.include_router(ScoreboardAPIRouter(ScoreboardServiceDB(test_db)).route())
    app.include_router(SeasonAPIRouter(SeasonServiceDB(test_db)).route())
    app.include_router(SponsorLineAPIRouter(SponsorLineServiceDB(test_db)).route())
    app.include_router(api_sponsor_sponsor_line_router)
    app.include_router(SponsorAPIRouter(SponsorServiceDB(test_db)).route())
    app.include_router(SportAPIRouter(SportServiceDB(test_db)).route())
    app.include_router(TeamTournamentRouter(TeamTournamentServiceDB(test_db)).route())
    app.include_router(TeamAPIRouter(TeamServiceDB(test_db)).route())
    app.include_router(TournamentAPIRouter(TournamentServiceDB(test_db)).route())

    yield app


@pytest_asyncio.fixture(scope="function")
async def client(test_app):
    """Create test client that uses app with test database."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
