import os
import shutil
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.core import settings
from src.core.models.base import Base, Database
from src.core.service_initialization import register_all_services
from src.core.service_registry import init_service_registry

db_url = settings.test_db.test_db_url

# Import fixtures from fixtures.py
pytest_plugins = ["tests.fixtures"]


# Custom markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks test as integration test (hits real website)"
    )
    config.addinivalue_line("markers", "benchmark: marks test as performance benchmark")
    config.addinivalue_line("markers", "e2e: marks test as end-to-end integration test")
    config.addinivalue_line("markers", "slow: marks test as slow-running")


# Database fixture that ensures a clean state using transactions, function-scoped
@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Database fixture that ensures a clean state using transactions."""
    db_url_str = str(db_url)
    assert "test" in db_url_str, "Test DB URL must contain 'test'"

    database = Database(db_url_str, echo=False)

    # Initialize service registry for each test with fresh database
    init_service_registry(database)
    register_all_services(database)

    # Create tables at start of each test (faster than migrations)
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Install pg_trgm extension for search optimization tests
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

        # Create GIN indexes for Person search optimization
        await conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS ix_person_first_name_trgm
            ON person USING GIN (first_name gin_trgm_ops)
        """)
        )

        await conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS ix_person_second_name_trgm
            ON person USING GIN (second_name gin_trgm_ops)
        """)
        )

        # Create Person search vector column and trigger
        await conn.execute(
            text("""
            ALTER TABLE person ADD COLUMN IF NOT EXISTS search_vector tsvector
        """)
        )

        await conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS ix_person_search_vector
            ON person USING GIN (search_vector)
        """)
        )

        await conn.execute(
            text("""
            CREATE OR REPLACE FUNCTION person_search_vector_update()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.search_vector :=
                    setweight(to_tsvector('english', COALESCE(NEW.first_name, '')), 'A') ||
                    setweight(to_tsvector('english', COALESCE(NEW.second_name, '')), 'A');
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """)
        )

        # Drop trigger if exists to avoid duplicate errors
        await conn.execute(
            text("""
            DROP TRIGGER IF EXISTS person_search_vector_trigger ON person
        """)
        )

        await conn.execute(
            text("""
            CREATE TRIGGER person_search_vector_trigger
            BEFORE INSERT OR UPDATE OF first_name, second_name ON person
            FOR EACH ROW
            EXECUTE FUNCTION person_search_vector_update()
        """)
        )

        # Create Team search components
        await conn.execute(
            text("""
            ALTER TABLE team ADD COLUMN IF NOT EXISTS search_vector tsvector
        """)
        )

        await conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS ix_team_search_vector
            ON team USING GIN (search_vector)
        """)
        )

        await conn.execute(
            text("""
            CREATE OR REPLACE FUNCTION team_search_vector_update()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.search_vector :=
                    to_tsvector('english', COALESCE(NEW.title, ''));
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """)
        )

        await conn.execute(
            text("""
            DROP TRIGGER IF EXISTS team_search_vector_trigger ON team
        """)
        )

        await conn.execute(
            text("""
            CREATE TRIGGER team_search_vector_trigger
            BEFORE INSERT OR UPDATE OF title ON team
            FOR EACH ROW
            EXECUTE FUNCTION team_search_vector_update()
        """)
        )

        await conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS ix_team_title_trgm
            ON team USING GIN (title gin_trgm_ops)
        """)
        )

    # Seed default roles
    from sqlalchemy import select

    from src.core.models.role import RoleDB

    async with database.async_session() as session:
        # Check if roles already exist (for parallel test execution)
        existing_roles = await session.execute(select(RoleDB.name))
        existing_names = {r[0] for r in existing_roles.fetchall()}

        if not existing_names:
            default_roles_data = [
                ("user", "Basic viewer role"),
                ("admin", "Administrator with full access"),
                ("editor", "Can edit content"),
                ("player", "Player account"),
                ("coach", "Coach account"),
                ("streamer", "Streamer account"),
            ]

            for name, description in default_roles_data:
                role = RoleDB(name=name, description=description)
                session.add(role)

            await session.commit()

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
    # Patch settings.uploads_path property
    from src.core.config import settings

    monkeypatch.setattr(
        type(settings), "uploads_path", property(lambda self: Path(test_downloads_dir))
    )
    return test_downloads_dir


@pytest_asyncio.fixture(scope="function")
async def test_app(test_db):
    """Create FastAPI test app with all routers."""
    from src.core.service_registry import init_service_registry

    # Re-initialize service registry for test environment
    init_service_registry(test_db)

    from src.auth.views import api_auth_router
    from src.football_events.db_services import FootballEventServiceDB
    from src.football_events.views import FootballEventAPIRouter
    from src.gameclocks.db_services import GameClockServiceDB
    from src.gameclocks.views import GameClockAPIRouter
    from src.matchdata.db_services import MatchDataServiceDB
    from src.matchdata.views import MatchDataAPIRouter
    from src.matches.crud_router import MatchCRUDRouter
    from src.matches.db_services import MatchServiceDB
    from src.matches.parser_router import MatchParserRouter
    from src.matches.websocket_router import MatchWebSocketRouter
    from src.person.db_services import PersonServiceDB
    from src.person.views import PersonAPIRouter
    from src.playclocks.db_services import PlayClockServiceDB
    from src.playclocks.views import PlayClockAPIRouter
    from src.player.db_services import PlayerServiceDB
    from src.player.views import PlayerAPIRouter
    from src.player_team_tournament.db_services import PlayerTeamTournamentServiceDB
    from src.player_team_tournament.views import PlayerTeamTournamentAPIRouter
    from src.positions.db_services import PositionServiceDB
    from src.positions.views import PositionAPIRouter
    from src.scoreboards.db_services import ScoreboardServiceDB
    from src.scoreboards.views import ScoreboardAPIRouter
    from src.seasons.db_services import SeasonServiceDB
    from src.seasons.views import SeasonAPIRouter
    from src.sponsor_lines.db_services import SponsorLineServiceDB
    from src.sponsor_lines.views import SponsorLineAPIRouter
    from src.sponsors.db_services import SponsorServiceDB
    from src.sponsors.views import SponsorAPIRouter
    from src.sports.db_services import SportServiceDB
    from src.sports.views import SportAPIRouter
    from src.team_tournament.db_services import TeamTournamentServiceDB
    from src.team_tournament.views import TeamTournamentRouter
    from src.teams.db_services import TeamServiceDB
    from src.teams.views import TeamAPIRouter
    from src.tournaments.db_services import TournamentServiceDB
    from src.tournaments.views import TournamentAPIRouter
    from src.users.db_services import UserServiceDB
    from src.users.views import UserAPIRouter, get_user_router

    app = FastAPI()
    match_service = MatchServiceDB(test_db)
    app.include_router(MatchCRUDRouter(match_service).route())
    app.include_router(MatchWebSocketRouter(match_service).route())
    app.include_router(MatchParserRouter(match_service).route())
    app.include_router(FootballEventAPIRouter(FootballEventServiceDB(test_db)).route())
    app.include_router(GameClockAPIRouter(GameClockServiceDB(test_db)).route())
    app.include_router(MatchDataAPIRouter(MatchDataServiceDB(test_db)).route())
    app.include_router(PersonAPIRouter(PersonServiceDB(test_db)).route())
    app.include_router(PlayClockAPIRouter(PlayClockServiceDB(test_db)).route())
    app.include_router(PlayerAPIRouter(PlayerServiceDB(test_db)).route())
    app.include_router(
        PlayerTeamTournamentAPIRouter(PlayerTeamTournamentServiceDB(test_db)).route()
    )
    app.include_router(PositionAPIRouter(PositionServiceDB(test_db)).route())
    app.include_router(ScoreboardAPIRouter(ScoreboardServiceDB(test_db)).route())
    app.include_router(SeasonAPIRouter(SeasonServiceDB(test_db)).route())
    app.include_router(SponsorLineAPIRouter(SponsorLineServiceDB(test_db)).route())
    app.include_router(SponsorAPIRouter(SponsorServiceDB(test_db)).route())
    app.include_router(SportAPIRouter(SportServiceDB(test_db)).route())
    app.include_router(TeamTournamentRouter(TeamTournamentServiceDB(test_db)).route())
    app.include_router(TeamAPIRouter(TeamServiceDB(test_db)).route())
    app.include_router(TournamentAPIRouter(TournamentServiceDB(test_db)).route())
    app.include_router(api_auth_router)
    app.include_router(UserAPIRouter(UserServiceDB(test_db)).route())
    app.include_router(get_user_router())

    # Import routers that are already instantiated at module level - not included in test app
    # from tests.fixtures import api_player_match_router, api_sponsor_sponsor_line_router
    # app.include_router(api_player_match_router)
    # app.include_router(api_sponsor_sponsor_line_router)

    yield app


@pytest_asyncio.fixture(scope="function")
async def client(test_app):
    """Create test client that uses app with test database."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
