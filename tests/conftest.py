import asyncio
import inspect
import shutil
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.core import settings
from src.core.models.base import Base, Database
from src.core.service_initialization import register_all_services
from src.core.service_registry import init_service_registry

# Import fixtures from fixtures.py
pytest_plugins = ["tests.fixtures"]

_SESSION_LOOP: asyncio.AbstractEventLoop | None = None


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks test as integration test (hits real website)"
    )
    config.addinivalue_line("markers", "e2e: marks test as end-to-end integration test")
    config.addinivalue_line("markers", "slow: marks test as slow-running")


def pytest_collection_modifyitems(config, items):
    """Ensure async tests use a session-scoped event loop."""
    for item in items:
        test_func = getattr(item, "obj", None) or getattr(item, "function", None)
        if test_func is not None and inspect.iscoroutinefunction(test_func):
            existing = item.get_closest_marker("asyncio")
            if existing is None or existing.kwargs.get("loop_scope") != "session":
                item.add_marker(pytest.mark.asyncio(loop_scope="session"), append=False)


def pytest_runtest_setup(item):
    """Ensure the session event loop is active for async tests."""
    if _SESSION_LOOP is not None:
        asyncio.set_event_loop(_SESSION_LOOP)


def get_db_url_for_worker(worker_id: str):
    """Get database URL based on worker ID."""
    base_url = str(settings.test_db.test_db_url)

    if worker_id == "master":
        return base_url

    worker_num = int(worker_id.replace("gw", ""))
    db_num = worker_num % 4

    if db_num == 1:
        return base_url.replace(settings.test_db.name, f"{settings.test_db.name}2")
    elif db_num == 2:
        return base_url.replace(settings.test_db.name, f"{settings.test_db.name}3")
    elif db_num == 3:
        return base_url.replace(settings.test_db.name, f"{settings.test_db.name}4")

    return base_url


@pytest.fixture(scope="session")
def worker_id(request):
    """Get the current worker ID."""
    if hasattr(request, "node") and hasattr(request.node, "workerinput"):
        return request.node.workerinput.get("workerid", "master")
    return "master"


@pytest.fixture(scope="session")
def test_db_url(worker_id):
    """Get database URL for the current worker."""
    return get_db_url_for_worker(worker_id)


async def _ensure_tables_created(db_url_str: str):
    """Ensure database tables and indexes are created using file-based lock."""
    import os

    from filelock import FileLock, Timeout

    # Create lock file based on database name to coordinate workers per database
    db_name = db_url_str.split("/")[-1]
    lock_file = f"/tmp/test_db_tables_setup_{db_name}.lock"
    setup_marker = f"/tmp/test_db_setup_complete_{db_name}.marker"

    try:
        with FileLock(lock_file, timeout=30):
            # Check if setup was already completed by another worker
            if os.path.exists(setup_marker):
                return

            assert "test" in db_url_str, "Test DB URL must contain 'test'"

            database = Database(db_url_str, echo=False)

            try:
                # Table and index creation (INSIDE lock)
                async with database.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

                    for index_sql in [
                        "CREATE INDEX IF NOT EXISTS ix_person_first_name_trgm ON person USING GIN (first_name gin_trgm_ops)",
                        "CREATE INDEX IF NOT EXISTS ix_person_second_name_trgm ON person USING GIN (second_name gin_trgm_ops)",
                        "CREATE INDEX IF NOT EXISTS ix_team_title_trgm ON team USING GIN (title gin_trgm_ops)",
                    ]:
                        try:
                            await conn.execute(text(index_sql))
                        except Exception:
                            pass

                # Role creation (NOW INSIDE LOCK - NO RACE CONDITION)
                from sqlalchemy import select

                from src.core.models.role import RoleDB

                async with database.async_session() as session:
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

                        await session.flush()

                # Mark setup as complete to prevent redundant operations
                Path(setup_marker).touch()
            finally:
                await database.close()
    # Lock released here AFTER all setup complete
    except Timeout:
        raise RuntimeError(
            f"Timeout waiting for database setup lock: {lock_file}. "
            "Another process may be holding the lock. "
            "Try clearing lock files: rm -f /tmp/test_db_*.lock"
        )


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def session_database(test_db_url: str) -> AsyncGenerator[Database, None]:
    """Session-scoped database instance shared within a worker."""
    await _ensure_tables_created(test_db_url)

    database = Database(test_db_url, echo=False, test_mode=True)
    init_service_registry(database)
    register_all_services(database)
    global _SESSION_LOOP
    _SESSION_LOOP = asyncio.get_running_loop()

    try:
        yield database
    finally:
        await database.close()


@pytest_asyncio.fixture(scope="function")
async def test_db(session_database: Database) -> AsyncGenerator[Database, None]:
    """Database fixture that ensures a clean state using transactions."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from src.core.service_registry import get_service_registry

    database = session_database
    get_service_registry().clear_singletons()

    async with database.engine.connect() as connection:
        transaction = await connection.begin()

        test_session_maker = async_sessionmaker(
            bind=connection,
            class_=database.async_session.class_,
            expire_on_commit=False,
        )

        database.test_async_session = test_session_maker

        try:
            yield database
        finally:
            if transaction.is_active:
                await transaction.rollback()
            database.test_async_session = None
            await connection.close()


@pytest.fixture(scope="session")
def test_downloads_dir():
    """Fixture to create and clean up test downloads directory."""
    downloads_dir = Path(__file__).parent / "test_downloads"

    downloads_dir.mkdir(parents=True, exist_ok=True)

    yield str(downloads_dir)

    if downloads_dir.exists():
        shutil.rmtree(downloads_dir)
        print(f"\nCleaned up test downloads directory: {downloads_dir}")


@pytest.fixture
def test_uploads_path(test_downloads_dir, monkeypatch):
    """Fixture to patch uploads_path for integration tests."""
    from src.core.config import settings

    monkeypatch.setattr(
        type(settings), "uploads_path", property(lambda self: Path(test_downloads_dir))
    )
    return test_downloads_dir


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def session_app(session_database):
    """Session-scoped FastAPI app - created once per worker.

    Routers are created with service=None and service_name, allowing lazy loading
    from the service registry which gets updated per test.

    Args:
        session_database: Session-scoped database that initializes the service registry
    """
    from src.auth.views import api_auth_router
    from src.core import health
    from src.football_events.views import FootballEventAPIRouter
    from src.gameclocks.views import GameClockAPIRouter
    from src.global_settings.views import GlobalSettingAPIRouter
    from src.matchdata.views import MatchDataAPIRouter
    from src.matches.crud_router import MatchCRUDRouter
    from src.matches.parser_router import MatchParserRouter
    from src.matches.websocket_router import MatchWebSocketRouter
    from src.person.views import PersonAPIRouter
    from src.playclocks.views import PlayClockAPIRouter
    from src.player.views import PlayerAPIRouter
    from src.player_match.views import PlayerMatchAPIRouter
    from src.player_team_tournament.views import PlayerTeamTournamentAPIRouter
    from src.positions.views import PositionAPIRouter
    from src.roles.views import RoleAPIRouter
    from src.scoreboards.views import ScoreboardAPIRouter
    from src.seasons.views import SeasonAPIRouter
    from src.sponsor_lines.views import SponsorLineAPIRouter
    from src.sponsors.views import SponsorAPIRouter
    from src.sports.views import SportAPIRouter
    from src.team_tournament.views import TeamTournamentRouter
    from src.teams.views import TeamAPIRouter
    from src.tournaments.views import TournamentAPIRouter
    from src.users.views import get_user_router

    app = FastAPI()

    app.include_router(MatchCRUDRouter(None, service_name="match").route())
    app.include_router(MatchWebSocketRouter(None, service_name="match").route())
    app.include_router(MatchParserRouter(None, service_name="match").route())
    app.include_router(FootballEventAPIRouter().route())
    app.include_router(GameClockAPIRouter().route())
    app.include_router(MatchDataAPIRouter().route())
    app.include_router(PersonAPIRouter().route())
    app.include_router(PlayClockAPIRouter(None, service_name="playclock").route())
    app.include_router(PlayerAPIRouter(None, service_name="player").route())
    app.include_router(PlayerMatchAPIRouter(None, service_name="player_match").route())
    app.include_router(
        PlayerTeamTournamentAPIRouter(None, service_name="player_team_tournament").route()
    )
    app.include_router(PositionAPIRouter().route())
    app.include_router(ScoreboardAPIRouter(None, service_name="scoreboard").route())
    app.include_router(SeasonAPIRouter().route())
    app.include_router(SponsorLineAPIRouter(None, service_name="sponsor_line").route())
    app.include_router(SponsorAPIRouter().route())
    app.include_router(SportAPIRouter().route())
    app.include_router(TeamTournamentRouter(None, service_name="team_tournament").route())
    app.include_router(TeamAPIRouter().route())
    app.include_router(TournamentAPIRouter(None, service_name="tournament").route())
    app.include_router(api_auth_router)
    app.include_router(GlobalSettingAPIRouter().route())
    app.include_router(get_user_router())
    app.include_router(health.router)

    try:
        role_router = RoleAPIRouter(None, service_name="role").route()
        app.include_router(role_router)
    except Exception as e:
        print(f"Error including role router: {e}")
        import traceback

        traceback.print_exc()

    yield app


@pytest_asyncio.fixture(scope="function")
async def test_app(session_app, test_db):
    """FastAPI test app with test database injected.

    Uses session-scoped app with service registry updated per test.
    """
    from src.core.service_registry import get_service_registry

    registry = get_service_registry()
    registry.update_database(test_db)

    yield session_app


@pytest_asyncio.fixture(scope="function")
async def client(test_app):
    """Create test client that uses app with test database."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
