import pytest

from src.core.models.base import Database
from src.logging_config import setup_logging
from src.seasons.db_services import SeasonServiceDB
from src.seasons.schemas import SeasonSchemaCreate
from src.sports.db_services import SportServiceDB
from src.sports.schemas import SportSchemaCreate
from src.tournaments.db_services import TournamentServiceDB
from src.tournaments.schemas import TournamentSchemaUpdate
from tests.factories import SeasonFactorySample, SportFactorySample, TournamentFactory

setup_logging()


@pytest.fixture(scope="function")
def sport(test_db: Database):
    return SportFactorySample.build()


@pytest.fixture(scope="function")
def season(test_db: Database):
    return SeasonFactorySample.build(year=2024)


@pytest.mark.asyncio
class TestTournamentServiceDBCreateOrUpdate:
    """Test create_or_update_tournament functionality."""

    async def test_create_tournament_with_eesl_id(
        self,
        test_db: Database,
        sport: SportSchemaCreate,
        season: SeasonSchemaCreate,
    ):
        """Test creating a tournament with eesl_id."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create(sport)

        season_service = SeasonServiceDB(test_db)
        created_season = await season_service.create(season)

        tournament_service = TournamentServiceDB(test_db)
        tournament_data = TournamentFactory.build(
            sport_id=created_sport.id,
            season_id=created_season.id,
            tournament_eesl_id=100,
            title="Test Tournament",
        )

        result = await tournament_service.create_or_update_tournament(tournament_data)

        assert result is not None
        assert result.id is not None
        assert result.tournament_eesl_id == 100
        assert result.title == "Test Tournament"

    async def test_create_tournament_without_eesl_id(
        self,
        test_db: Database,
        sport: SportSchemaCreate,
        season: SeasonSchemaCreate,
    ):
        """Test creating a tournament without eesl_id."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create(sport)

        season_service = SeasonServiceDB(test_db)
        created_season = await season_service.create(season)

        tournament_service = TournamentServiceDB(test_db)
        tournament_data = TournamentFactory.build(
            sport_id=created_sport.id,
            season_id=created_season.id,
            tournament_eesl_id=None,
            title="Tournament Without EESL",
        )

        result = await tournament_service.create_or_update_tournament(tournament_data)

        assert result is not None
        assert result.id is not None
        assert result.tournament_eesl_id is None
        assert result.title == "Tournament Without EESL"

    async def test_update_existing_tournament_by_eesl_id(
        self,
        test_db: Database,
        sport: SportSchemaCreate,
        season: SeasonSchemaCreate,
    ):
        """Test updating an existing tournament by eesl_id."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create(sport)

        season_service = SeasonServiceDB(test_db)
        created_season = await season_service.create(season)

        tournament_service = TournamentServiceDB(test_db)

        tournament_data = TournamentFactory.build(
            sport_id=created_sport.id,
            season_id=created_season.id,
            tournament_eesl_id=200,
            title="Original Title",
        )
        created = await tournament_service.create_or_update_tournament(tournament_data)

        update_data = TournamentSchemaUpdate(
            tournament_eesl_id=200, title="Updated Title", description="New Description"
        )

        updated = await tournament_service.create_or_update_tournament(update_data)

        assert updated.id == created.id
        assert updated.title == "Updated Title"
        assert updated.description == "New Description"

    async def test_create_multiple_tournaments(
        self,
        test_db: Database,
        sport: SportSchemaCreate,
        season: SeasonSchemaCreate,
    ):
        """Test creating multiple tournaments."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create(sport)

        season_service = SeasonServiceDB(test_db)
        created_season = await season_service.create(season)

        tournament_service = TournamentServiceDB(test_db)

        tournament1_data = TournamentFactory.build(
            sport_id=created_sport.id,
            season_id=created_season.id,
            tournament_eesl_id=301,
        )
        tournament2_data = TournamentFactory.build(
            sport_id=created_sport.id,
            season_id=created_season.id,
            tournament_eesl_id=302,
        )

        tournament1 = await tournament_service.create_or_update_tournament(
            tournament1_data
        )
        tournament2 = await tournament_service.create_or_update_tournament(
            tournament2_data
        )

        assert tournament1.tournament_eesl_id == 301
        assert tournament2.tournament_eesl_id == 302
        assert tournament1.id != tournament2.id

    async def test_update_tournament_partial_fields(
        self,
        test_db: Database,
        sport: SportSchemaCreate,
        season: SeasonSchemaCreate,
    ):
        """Test updating only some tournament fields."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create(sport)

        season_service = SeasonServiceDB(test_db)
        created_season = await season_service.create(season)

        tournament_service = TournamentServiceDB(test_db)

        tournament_data = TournamentFactory.build(
            sport_id=created_sport.id,
            season_id=created_season.id,
            tournament_eesl_id=400,
            title="Full Title",
            description="Original Description",
        )
        created = await tournament_service.create_or_update_tournament(tournament_data)

        update_data = TournamentSchemaUpdate(
            tournament_eesl_id=400, description="Updated Description"
        )

        updated = await tournament_service.create_or_update_tournament(update_data)

        assert updated.id == created.id
        assert updated.title == "Full Title"
        assert updated.description == "Updated Description"

    async def test_upsert_create_then_update(
        self,
        test_db: Database,
        sport: SportSchemaCreate,
        season: SeasonSchemaCreate,
    ):
        """Test creating then updating same tournament in sequence."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create(sport)

        season_service = SeasonServiceDB(test_db)
        created_season = await season_service.create(season)

        tournament_service = TournamentServiceDB(test_db)

        create_data = TournamentFactory.build(
            sport_id=created_sport.id,
            season_id=created_season.id,
            tournament_eesl_id=500,
            title="Create Title",
        )
        created = await tournament_service.create_or_update_tournament(create_data)

        update_data = TournamentSchemaUpdate(
            tournament_eesl_id=500, title="Update Title"
        )
        updated = await tournament_service.create_or_update_tournament(update_data)

        assert created.id == updated.id
        assert created.title == "Create Title"
        assert updated.title == "Update Title"

    async def test_get_tournament_by_eesl_id(
        self,
        test_db: Database,
        sport: SportSchemaCreate,
        season: SeasonSchemaCreate,
    ):
        """Test retrieving tournament by eesl_id."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create(sport)

        season_service = SeasonServiceDB(test_db)
        created_season = await season_service.create(season)

        tournament_service = TournamentServiceDB(test_db)

        tournament_data = TournamentFactory.build(
            sport_id=created_sport.id,
            season_id=created_season.id,
            tournament_eesl_id=600,
            title="Get Tournament",
        )
        created = await tournament_service.create_or_update_tournament(tournament_data)

        retrieved = await tournament_service.get_tournament_by_eesl_id(600)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Get Tournament"
