import logging

import pytest
import pytest_asyncio

from src.global_settings.db_services import GlobalSettingServiceDB
from src.person.db_services import PersonServiceDB
from src.positions.db_services import PositionServiceDB
from src.seasons.db_services import SeasonServiceDB
from src.sponsor_lines.db_services import SponsorLineServiceDB
from src.sponsors.db_services import SponsorServiceDB
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import (
    PositionFactory,
    SeasonFactorySample,
    SponsorFactory,
    SponsorLineFactory,
    SportFactorySample,
    TeamFactory,
    TournamentFactory,
)

test_logger = logging.getLogger("backend_logger_tests")


@pytest_asyncio.fixture()
async def test_person_service(test_db) -> PersonServiceDB:
    return PersonServiceDB(test_db)


@pytest_asyncio.fixture()
async def test_season_service(test_db) -> SeasonServiceDB:
    return SeasonServiceDB(test_db)


@pytest_asyncio.fixture()
async def test_sport_service(test_db) -> SportServiceDB:
    return SportServiceDB(test_db)


@pytest_asyncio.fixture()
async def test_tournament_service(test_db) -> TournamentServiceDB:
    return TournamentServiceDB(test_db)


@pytest_asyncio.fixture()
async def test_team_service(test_db) -> TeamServiceDB:
    return TeamServiceDB(test_db)


@pytest_asyncio.fixture
async def season(test_season_service):
    """Create and return a season instance in the database."""
    test_logger.info("Creating test season")
    data = SeasonFactorySample.build()
    season = await test_season_service.create(data)
    return season


@pytest_asyncio.fixture
async def sport(test_sport_service):
    """Create and return a sport instance in the database."""
    test_logger.info("Creating test sport")
    data = SportFactorySample.build()
    sport = await test_sport_service.create(data)
    return sport


@pytest_asyncio.fixture
async def tournament(test_tournament_service, sport, season):
    """Create and return a tournament instance in the database."""
    test_logger.info(
        f"Creating test tournament with sport_id: {sport.id} and season_id: {season.id}"
    )
    data = TournamentFactory.build(sport_id=sport.id, season_id=season.id)
    tournament = await test_tournament_service.create(data)
    return tournament


@pytest_asyncio.fixture
async def teams_data(test_team_service, sport):
    """Create and return two test teams in the database."""
    test_logger.info(f"Creating test teams with sport_id: {sport.id}")
    team1 = TeamFactory.build(sport_id=sport.id, team_eesl_id=801, title="Team A")
    team2 = TeamFactory.build(sport_id=sport.id, team_eesl_id=802, title="Team B")
    created_team1 = await test_team_service.create_or_update_team(team1)
    created_team2 = await test_team_service.create_or_update_team(team2)
    return created_team1, created_team2


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
        tournament = await test_tournament_service.create(data)
        tournaments_list.append(tournament)
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


@pytest.fixture(scope="function")
def season_db_model():
    """Return a SeasonDB model instance for testing (not a schema)."""
    from src.core.models.season import SeasonDB

    return SeasonDB(year=2024, description="Test Season")


@pytest_asyncio.fixture()
async def test_position_service(test_db) -> PositionServiceDB:
    return PositionServiceDB(test_db)


@pytest_asyncio.fixture()
async def test_sponsor_service(test_db) -> SponsorServiceDB:
    return SponsorServiceDB(test_db)


@pytest_asyncio.fixture()
async def test_global_setting_service(test_db) -> GlobalSettingServiceDB:
    return GlobalSettingServiceDB(test_db)


@pytest_asyncio.fixture()
async def test_sponsor_line_service(test_db) -> SponsorLineServiceDB:
    return SponsorLineServiceDB(test_db)


@pytest_asyncio.fixture
async def position(test_position_service, sport):
    """Create and return a position instance in database."""
    test_logger.info("Creating test position")
    data = PositionFactory.build(sport_id=sport.id)
    position = await test_position_service.create(data)
    return position


@pytest_asyncio.fixture
async def sponsor(test_sponsor_service):
    """Create and return a sponsor instance in database."""
    test_logger.info("Creating test sponsor")
    data = SponsorFactory.build()
    sponsor = await test_sponsor_service.create(data)
    return sponsor


@pytest_asyncio.fixture
async def sponsor_line(test_sponsor_line_service):
    """Create and return a sponsor line instance in database."""
    test_logger.info("Creating test sponsor line")
    data = SponsorLineFactory.build()
    sponsor_line = await test_sponsor_line_service.create(data)
    return sponsor_line


@pytest.fixture(scope="function")
def temp_file_with_cyrillic_name(tmp_path):
    """Create a temporary file with Cyrillic filename for testing."""
    filename = "команда.jpg"
    file_path = tmp_path / filename
    file_path.write_text("test content")
    return {
        "original_filename": filename,
        "file_path": file_path,
        "converted_filename": "komanda.jpg",
    }


@pytest.fixture(scope="function")
def temp_files_with_various_cyrillic_names(tmp_path):
    """Create multiple temporary files with various Cyrillic filenames for testing."""
    test_cases = [
        {
            "original": "команда.jpg",
            "converted": "komanda.jpg",
        },
        {
            "original": "Турнир 2023.png",
            "converted": "Turnir_2023.png",
        },
        {
            "original": "Фото команды.jpeg",
            "converted": "Foto_komandy.jpeg",
        },
        {
            "original": "Тестовый_файл.txt",
            "converted": "Testovyy_fayl.txt",
        },
        {
            "original": "Безрасширения",
            "converted": "Bezrasshireniya",
        },
    ]

    created_files = []
    for case in test_cases:
        file_path = tmp_path / case["original"]
        file_path.write_text("test content")
        created_files.append(
            {
                "original_filename": case["original"],
                "file_path": file_path,
                "converted_filename": case["converted"],
            }
        )

    return created_files
