import logging

import pytest_asyncio

from src.logging_config import setup_logging
from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import SportFactorySample, SeasonFactorySample, TournamentFactory
from tests.testhelpers import create_test_entity

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
async def tournament(test_tournament_service, sport, season):
    """Create and return a tournament instance in the database."""
    try:
        test_logger.info(
            f"Creating test tournament with sport_id: {sport.id} and season_id: {season.id}"
        )
        data = TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        tournament = await test_tournament_service.create_new_tournament(data)
        return tournament
    except Exception as e:
        test_logger.error(f"Error creating test tournament {e}", exc_info=True)


# @pytest_asyncio.fixture
# async def tournament(test_db, sport, season):
#     """Create and return a tournament instance with the sport and season."""
#     # Pass sport_id and season_id to the factory to ensure they're set correctly
#     return await create_test_entity(
#         TournamentFactory(sport=sport, season=season),
#         test_db,
#     )


# @pytest_asyncio.fixture
# async def tournament(test_db, sport, season):
#     """Create and return a tournament instance with the sport and season."""
#     print(
#         f"Creating tournament instance with sport_id: {sport.id} and season_id: {season.id}"
#     )
#
#     # Set the foreign keys directly, without using the SubFactory
#     tournament_instance = TournamentFactory.build(
#         sport_id=sport.id, season_id=season.id
#     )
#
#     print(f"Tournament created with ID: {tournament_instance.id}")
#
#     # Now add it to the database and return the entity
#     return await create_test_entity(tournament_instance, test_db)
