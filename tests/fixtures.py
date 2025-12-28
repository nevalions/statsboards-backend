import logging

import pytest
import pytest_asyncio

from src.logging_config import setup_logging
from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import SportFactorySample, SeasonFactorySample, TournamentFactory


setup_logging()
test_logger = logging.getLogger("backend_logger_tests")


@pytest_asyncio.fixture()
async def test_season_service(test_db) -> SeasonServiceDB:
    return SeasonServiceDB(test_db)


@pytest_asyncio.fixture()
async def test_sport_service(test_db) -> SportServiceDB:
    return SportServiceDB(test_db)


@pytest_asyncio.fixture()
async def test_tournament_service(test_db) -> TournamentServiceDB:
    return TournamentServiceDB(test_db)


@pytest_asyncio.fixture
async def season(test_season_service):
    """Create and return a season instance in the database."""
    try:
        test_logger.info(f"Creating test season")
        data = SeasonFactorySample.build()
        season = await test_season_service.create_season(data)
        return season
    except Exception as e:
        test_logger.error(f"Error creating test season {e}", exc_info=True)


@pytest_asyncio.fixture
async def sport(test_sport_service):
    """Create and return a sport instance in the database."""
    try:
        test_logger.info(f"Creating test sport")
        data = SportFactorySample.build()
        sport = await test_sport_service.create_sport(data)
        return sport
    except Exception as e:
        test_logger.error(f"Error creating test sport {e}", exc_info=True)


@pytest_asyncio.fixture
async def tournament(test_tournament_service, sport, season):
    """Create and return a tournament instance in the database."""
    try:
        test_logger.info(
            f"Creating test tournament with sport_id: {sport.id} and season_id: {season.id}"
        )
        data = TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        tournament = await test_tournament_service.create_tournament(data)
        return tournament
    except Exception as e:
        test_logger.error(f"Error creating test tournament {e}", exc_info=True)


async def creat_tournaments(
    test_tournament_service,
    sport,
    season,
    count=1,
):
    """Create and return a list of unique tournament instances."""
    tournaments_list = []
    for i in range(count):
        test_logger.info(
            f"Creating test tournament {i + 1} with sport_id: {sport.id} and season_id: {season.id}"
        )
        data = TournamentFactory.build(
            sport_id=sport.id,
            season_id=season.id,
            title=f"Tournament {i + 1}",  # Ensure unique title
        )
        try:
            tournament = await test_tournament_service.create_tournament(data)
            tournaments_list.append(tournament)
        except Exception as e:
            test_logger.error(
                f"Error creating test tournament {i + 1}: {e}", exc_info=True
            )
    return tournaments_list


@pytest_asyncio.fixture
async def tournaments(test_tournament_service, sport, season):
    """Create and return multiple tournament instances."""
    return await creat_tournaments(test_tournament_service, sport, season, count=5)

@pytest.fixture(scope="function")
def season_sample():
    """Return a season schema sample for testing."""
    return SeasonFactorySample.build()


@pytest.fixture(scope="function")
def sport_sample():
    """Return a sport schema sample for testing."""
    return SportFactorySample.build()
