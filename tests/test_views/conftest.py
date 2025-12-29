import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from src.core.config import settings
from src.core.models.base import Database, Base

db_url = str(settings.test_db.test_db_url)

_tables_created = False


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Database fixture for view tests using transactions."""
    global _tables_created

    assert "test" in db_url, "Test DB URL must contain 'test'"
    database = Database(db_url, echo=False)

    if not _tables_created:
        async with database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        _tables_created = True

    async with database.engine.connect() as connection:
        transaction = await connection.begin()
        database.async_session.configure(bind=connection)

        try:
            yield database
            if transaction.is_active:
                await transaction.rollback()
        finally:
            pass


@pytest_asyncio.fixture(scope="function")
async def test_app(test_db):
    """Create FastAPI app with test database by creating new router instances."""
    app = FastAPI()

    from src.football_events.views import FootballEventAPIRouter
    from src.seasons.views import SeasonAPIRouter
    from src.sports.views import SportAPIRouter
    from src.teams.views import TeamAPIRouter
    from src.matches.views import MatchAPIRouter
    from src.tournaments.views import TournamentAPIRouter
    from src.positions.views import PositionAPIRouter
    from src.sponsors.views import SponsorAPIRouter
    from src.sponsor_lines.views import SponsorLineAPIRouter
    from src.sponsor_sponsor_line_connection.views import SponsorSponsorLineAPIRouter
    from src.gameclocks.views import GameClockAPIRouter
    from src.playclocks.views import PlayClockAPIRouter
    from src.matchdata.views import MatchDataAPIRouter
    from src.person.views import PersonAPIRouter
    from src.player.views import PlayerAPIRouter
    from src.player_match.views import PlayerMatchAPIRouter
    from src.player_team_tournament.views import PlayerTeamTournamentAPIRouter
    from src.scoreboards.views import ScoreboardAPIRouter
    from src.team_tournament.views import TeamTournamentRouter

    from src.football_events.db_services import FootballEventServiceDB
    from src.seasons.db_services import SeasonServiceDB
    from src.sports.db_services import SportServiceDB
    from src.teams.db_services import TeamServiceDB
    from src.matches.db_services import MatchServiceDB
    from src.tournaments.db_services import TournamentServiceDB
    from src.positions.db_services import PositionServiceDB
    from src.sponsors.db_services import SponsorServiceDB
    from src.sponsor_lines.db_services import SponsorLineServiceDB
    from src.sponsor_sponsor_line_connection.db_services import SponsorSponsorLineServiceDB
    from src.gameclocks.db_services import GameClockServiceDB
    from src.playclocks.db_services import PlayClockServiceDB
    from src.matchdata.db_services import MatchDataServiceDB
    from src.person.db_services import PersonServiceDB
    from src.player.db_services import PlayerServiceDB
    from src.player_match.db_services import PlayerMatchServiceDB
    from src.player_team_tournament.db_services import PlayerTeamTournamentServiceDB
    from src.scoreboards.db_services import ScoreboardServiceDB
    from src.team_tournament.db_services import TeamTournamentServiceDB

    app.include_router(FootballEventAPIRouter(FootballEventServiceDB(test_db)).route())
    app.include_router(SeasonAPIRouter(SeasonServiceDB(test_db)).route())
    app.include_router(SportAPIRouter(SportServiceDB(test_db)).route())
    app.include_router(TeamAPIRouter(TeamServiceDB(test_db)).route())
    app.include_router(MatchAPIRouter(MatchServiceDB(test_db)).route())
    app.include_router(TournamentAPIRouter(TournamentServiceDB(test_db)).route())
    app.include_router(PositionAPIRouter(PositionServiceDB(test_db)).route())
    app.include_router(SponsorAPIRouter(SponsorServiceDB(test_db)).route())
    app.include_router(SponsorLineAPIRouter(SponsorLineServiceDB(test_db)).route())
    app.include_router(SponsorSponsorLineAPIRouter(SponsorSponsorLineServiceDB(test_db)).route())
    app.include_router(GameClockAPIRouter(GameClockServiceDB(test_db, disable_background_tasks=True)).route())
    app.include_router(PlayClockAPIRouter(PlayClockServiceDB(test_db, disable_background_tasks=True)).route())
    app.include_router(MatchDataAPIRouter(MatchDataServiceDB(test_db)).route())
    app.include_router(PersonAPIRouter(PersonServiceDB(test_db)).route())
    app.include_router(PlayerAPIRouter(PlayerServiceDB(test_db)).route())
    app.include_router(PlayerMatchAPIRouter(PlayerMatchServiceDB(test_db)).route())
    app.include_router(PlayerTeamTournamentAPIRouter(PlayerTeamTournamentServiceDB(test_db)).route())
    app.include_router(ScoreboardAPIRouter(ScoreboardServiceDB(test_db)).route())
    app.include_router(TeamTournamentRouter(TeamTournamentServiceDB(test_db)).route())

    yield app


@pytest_asyncio.fixture(scope="function")
async def client(test_app):
    """Create test client that uses app with test database."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
