import pytest
import pytest_asyncio


from src.tournaments.db_services import TournamentServiceDB
from src.tournaments.schemas import (
    TournamentSchemaCreate,
    TournamentSchemaUpdate,
    TournamentSchemaBase,
)


# Fixture to provide an instance of TournamentServiceDB with session
@pytest_asyncio.fixture(scope="function")
async def tournament_service(test_db):
    """Fixture to provide an instance of TournamentServiceDB with session."""
    service = TournamentServiceDB(test_db)  # Pass the engine or async session
    return service


# Fixture to provide sample tournament data
@pytest.fixture(scope="function")
def sample_tournament_data() -> TournamentSchemaCreate:
    """Fixture to provide sample tournament data."""
    return TournamentSchemaCreate(
        tournament_eesl_id=111,
        title="Tournament A",
        description="Description of tournament A",
        tournament_logo_url="logo_url",
        tournament_logo_icon_url="icon_logo_url",
        tournament_logo_web_url="web_logo_url",
        season_id=None,
        sport_id=None,
        sponsor_line_id=None,
        main_sponsor_id=None,
    )


# Test class for TournamentServiceDB
@pytest.mark.asyncio
class TestTournamentServiceDB:
    async def test_create_tournament_success(
        self, tournament_service, sample_tournament_data
    ):
        """Test successful tournament creation."""
        created_tournament: TournamentSchemaBase = (
            await tournament_service.create_or_update_tournament(sample_tournament_data)
        )

        assert created_tournament is not None
        assert (
            created_tournament.tournament_eesl_id
            == sample_tournament_data.tournament_eesl_id
        )
        assert created_tournament.title == sample_tournament_data.title
        assert created_tournament.description == sample_tournament_data.description
        assert (
            created_tournament.tournament_logo_url
            == sample_tournament_data.tournament_logo_url
        )
        assert (
            created_tournament.tournament_logo_icon_url
            == sample_tournament_data.tournament_logo_icon_url
        )
        assert (
            created_tournament.tournament_logo_web_url
            == sample_tournament_data.tournament_logo_web_url
        )
        assert created_tournament.season_id == sample_tournament_data.season_id
        assert created_tournament.sport_id == sample_tournament_data.sport_id
        assert (
            created_tournament.main_sponsor_id == sample_tournament_data.main_sponsor_id
        )
        assert created_tournament.title == "Tournament A"
