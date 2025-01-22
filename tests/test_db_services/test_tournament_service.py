import pytest
import pytest_asyncio


from src.tournaments.db_services import TournamentServiceDB
from tests.factories import TournamentFactory, SportFactory, SeasonFactorySample


# Fixture to provide an instance of TournamentServiceDB with session
@pytest_asyncio.fixture(scope="function")
async def tournament_service(test_db):
    """Fixture to provide an instance of TournamentServiceDB with session."""
    service = TournamentServiceDB(test_db)  # Pass the engine or async session
    return service


@pytest_asyncio.fixture
async def sport(test_db):
    """Create and return a sport instance in the database."""
    sport_obj = SportFactory.build()
    async with test_db.async_session() as session:
        session.add(sport_obj)
        await session.commit()
        await session.refresh(sport_obj)
        return sport_obj


@pytest_asyncio.fixture
async def season(test_db):
    """Create and return a season instance in the database."""
    season_obj = SeasonFactorySample.build()
    async with test_db.async_session() as session:
        session.add(season_obj)
        await session.commit()
        await session.refresh(season_obj)
        return season_obj


@pytest.mark.asyncio
class TestTournamentServiceDB:
    async def test_create_tournament_with_relations(
        self,
        tournament_service: TournamentServiceDB,
        sport,
        season,
    ):
        """Test creating a tournament with related sport and season."""
        # Create tournament data with existing sport and season
        tournament_data = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id
        )

        # Create the tournament
        created_tournament = await tournament_service.create_new_tournament(
            tournament_data
        )

        # Verify the tournament was created with correct relations
        assert created_tournament.sport_id == sport.id
        assert created_tournament.season_id == season.id
        assert created_tournament.title == tournament_data.title


#
# # Test class for TournamentServiceDB
# @pytest.mark.asyncio
# class TestTournamentServiceDB:
#     async def test_create_tournament_success(
#         self, tournament_service, sample_tournament_data
#     ):
#         """Test successful tournament creation."""
#         created_tournament: TournamentSchemaBase = (
#             await tournament_service.create_or_update_tournament(sample_tournament_data)
#         )
#
#         assert created_tournament is not None
#         assert (
#             created_tournament.tournament_eesl_id
#             == sample_tournament_data.tournament_eesl_id
#         )
#         assert created_tournament.title == sample_tournament_data.title
#         assert created_tournament.description == sample_tournament_data.description
#         assert (
#             created_tournament.tournament_logo_url
#             == sample_tournament_data.tournament_logo_url
#         )
#         assert (
#             created_tournament.tournament_logo_icon_url
#             == sample_tournament_data.tournament_logo_icon_url
#         )
#         assert (
#             created_tournament.tournament_logo_web_url
#             == sample_tournament_data.tournament_logo_web_url
#         )
#         assert created_tournament.season_id == sample_tournament_data.season_id
#         assert created_tournament.sport_id == sample_tournament_data.sport_id
#         assert (
#             created_tournament.main_sponsor_id == sample_tournament_data.main_sponsor_id
#         )
#         assert created_tournament.title == "Tournament A"
