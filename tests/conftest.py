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

# Import fixtures from fixtures.py
pytest_plugins = ["tests.fixtures"]


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks test as integration test (hits real website)"
    )
    config.addinivalue_line("markers", "e2e: marks test as end-to-end integration test")
    config.addinivalue_line("markers", "slow: marks test as slow-running")


def get_db_url_for_worker(worker_id: str):
    """Get database URL based on worker ID."""
    base_url = str(settings.test_db.test_db_url)

    if worker_id == "master":
        return base_url

    worker_num = int(worker_id.replace("gw", ""))
    db_num = worker_num % 2

    if db_num == 1:
        return base_url.replace(settings.test_db.name, f"{settings.test_db.name}2")

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
    import fcntl

    # Create lock file based on database name to coordinate workers per database
    db_name = db_url_str.split("/")[-1]
    lock_file = f"/tmp/test_db_tables_setup_{db_name}.lock"

    with open(lock_file, "w") as f:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        except (ImportError, AttributeError):
            pass

        assert "test" in db_url_str, "Test DB URL must contain 'test'"

        database = Database(db_url_str, echo=False)

        try:
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
        finally:
            await database.close()


@pytest_asyncio.fixture(scope="function")
async def test_db(test_db_url):
    """Database fixture that ensures a clean state using transactions."""
    await _ensure_tables_created(test_db_url)

    database = Database(test_db_url, echo=False, test_mode=True)

    init_service_registry(database)
    register_all_services(database)

    async with database.engine.connect() as connection:
        transaction = await connection.begin()
        database.async_session.configure(bind=connection)

        try:
            yield database
            if transaction.is_active:
                await transaction.rollback()
        finally:
            await connection.close()
            await database.close()


@pytest.fixture(scope="session")
def test_downloads_dir():
    """Fixture to create and clean up test downloads directory."""
    downloads_dir = os.path.join(os.path.dirname(__file__), "test_downloads")

    os.makedirs(downloads_dir, exist_ok=True)

    yield downloads_dir

    if os.path.exists(downloads_dir):
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


@pytest_asyncio.fixture(scope="function")
async def test_app(test_db):
    """Create FastAPI test app with all routers."""
    from src.core.service_registry import init_service_registry

    init_service_registry(test_db)

    from src.auth.views import api_auth_router
    from src.core import health
    from src.football_events.db_services import FootballEventServiceDB
    from src.football_events.views import FootballEventAPIRouter
    from src.gameclocks.db_services import GameClockServiceDB
    from src.gameclocks.views import GameClockAPIRouter
    from src.global_settings.db_services import GlobalSettingServiceDB
    from src.global_settings.views import GlobalSettingAPIRouter
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
    from src.roles.db_services import RoleServiceDB
    from src.roles.views import RoleAPIRouter
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
    from src.users.views import get_user_router

    app = FastAPI()
    match_service = MatchServiceDB(test_db)
    app.include_router(MatchCRUDRouter(match_service).route())
    app.include_router(MatchWebSocketRouter(match_service).route())
    app.include_router(MatchParserRouter(match_service).route())
    app.include_router(FootballEventAPIRouter().route())
    app.include_router(GameClockAPIRouter().route())
    app.include_router(MatchDataAPIRouter().route())
    app.include_router(PersonAPIRouter().route())
    app.include_router(PlayClockAPIRouter(PlayClockServiceDB(test_db)).route())
    app.include_router(PlayerAPIRouter(PlayerServiceDB(test_db)).route())
    app.include_router(
        PlayerTeamTournamentAPIRouter(PlayerTeamTournamentServiceDB(test_db)).route()
    )
    app.include_router(PositionAPIRouter().route())
    app.include_router(ScoreboardAPIRouter(ScoreboardServiceDB(test_db)).route())
    app.include_router(SeasonAPIRouter().route())
    app.include_router(SponsorLineAPIRouter(SponsorLineServiceDB(test_db)).route())
    app.include_router(SponsorAPIRouter().route())
    app.include_router(SportAPIRouter().route())
    app.include_router(TeamTournamentRouter(TeamTournamentServiceDB(test_db)).route())
    app.include_router(TeamAPIRouter().route())
    app.include_router(TournamentAPIRouter(TournamentServiceDB(test_db)).route())
    app.include_router(api_auth_router)
    app.include_router(GlobalSettingAPIRouter().route())
    app.include_router(get_user_router())
    app.include_router(health.router)
    try:
        role_router = RoleAPIRouter(RoleServiceDB(test_db)).route()
        app.include_router(role_router)
        print("Role routes:")
        for route in role_router.routes:
            print(f"  {route.path} - {route.methods}")
    except Exception as e:
        print(f"Error including role router: {e}")
        import traceback

        traceback.print_exc()

    print("All app routes:")
    for route in app.routes:
        print(f"  {route.path}")

    yield app


@pytest_asyncio.fixture(scope="function")
async def client(test_app):
    """Create test client that uses app with test database."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
