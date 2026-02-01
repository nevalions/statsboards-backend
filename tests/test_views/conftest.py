import fcntl
from pathlib import Path
from typing import AsyncGenerator

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.core.models.base import Base, Database
from src.core.service_initialization import register_all_services
from src.core.service_registry import init_service_registry


async def _ensure_tables_created(db_url: str):
    """Ensure database tables and indexes are created using file-based lock."""
    from filelock import FileLock, Timeout

    db_name = db_url.rsplit("/", 1)[-1]
    lock_file = f"/tmp/test_db_tables_setup_{db_name}.lock"
    setup_marker = f"/tmp/test_db_setup_complete_{db_name}.marker"

    if Path(setup_marker).exists():
        return

    try:
        with FileLock(lock_file, timeout=30):
            if Path(setup_marker).exists():
                return

            assert "test" in db_url, "Test DB URL must contain 'test'"

            database = Database(db_url, echo=False)

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

                Path(setup_marker).touch()
            finally:
                await database.close()
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

    assert "test" in test_db_url, "Test DB URL must contain 'test'"
    database = Database(test_db_url, echo=False, test_mode=True)

    init_service_registry(database)
    register_all_services(database)

    try:
        yield database
    finally:
        await database.close()


@pytest_asyncio.fixture(scope="function")
async def test_db(session_database: Database) -> AsyncGenerator[Database, None]:
    """Database fixture for view tests using transactions."""
    from src.core.service_registry import get_service_registry

    database = session_database
    get_service_registry().clear_singletons()

    # Use a transactional connection for tests
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


@pytest_asyncio.fixture(scope="function")
async def test_app(test_db):
    """Create FastAPI app with test database by creating new router instances."""
    app = FastAPI()

    from src.core.health import router as health_router
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
    from src.player_match.db_services import PlayerMatchServiceDB
    from src.player_match.views import PlayerMatchAPIRouter
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
    from src.sponsor_sponsor_line_connection.db_services import (
        SponsorSponsorLineServiceDB,
    )
    from src.sponsor_sponsor_line_connection.views import SponsorSponsorLineAPIRouter
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

    app.include_router(health_router)
    app.include_router(FootballEventAPIRouter().route())
    app.include_router(SeasonAPIRouter().route())
    app.include_router(SportAPIRouter().route())
    app.include_router(TeamAPIRouter().route())
    app.include_router(MatchCRUDRouter(MatchServiceDB(test_db)).route())
    app.include_router(MatchWebSocketRouter(MatchServiceDB(test_db)).route())
    app.include_router(MatchParserRouter(MatchServiceDB(test_db)).route())
    app.include_router(TournamentAPIRouter(TournamentServiceDB(test_db)).route())
    app.include_router(PositionAPIRouter().route())
    app.include_router(SponsorAPIRouter().route())
    app.include_router(SponsorLineAPIRouter(SponsorLineServiceDB(test_db)).route())
    app.include_router(SponsorSponsorLineAPIRouter(SponsorSponsorLineServiceDB(test_db)).route())
    app.include_router(GameClockAPIRouter().route())
    app.include_router(PlayClockAPIRouter(PlayClockServiceDB(test_db)).route())
    app.include_router(MatchDataAPIRouter().route())
    app.include_router(PersonAPIRouter().route())
    app.include_router(PlayerAPIRouter(PlayerServiceDB(test_db)).route())
    app.include_router(PlayerMatchAPIRouter(PlayerMatchServiceDB(test_db)).route())
    app.include_router(
        PlayerTeamTournamentAPIRouter(PlayerTeamTournamentServiceDB(test_db)).route()
    )
    app.include_router(ScoreboardAPIRouter(ScoreboardServiceDB(test_db)).route())
    app.include_router(TeamTournamentRouter(TeamTournamentServiceDB(test_db)).route())

    yield app


@pytest_asyncio.fixture(scope="function")
async def client(test_app):
    """Create test client that uses app with test database."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
