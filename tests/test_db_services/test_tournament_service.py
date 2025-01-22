import pytest
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import TournamentFactory
from tests.fixtures import (
    test_tournament_service,
    test_sport_service,
    test_season_service,
    tournament,
    sport,
    season,
)


@pytest.fixture(scope="function")
def tournament_sample(sport, season):
    return TournamentFactory.build(sport_id=sport.id, season_id=season.id)


@pytest.mark.asyncio
class TestTournamentServiceDB:
    async def test_create_tournament_with_relations(
        self,
        test_tournament_service: TournamentServiceDB,
        sport,
        season,
        tournament_sample,
    ):
        """Test creating a tournament with related sport and season."""
        # Create the tournament
        created_tournament = await test_tournament_service.create_tournament(
            tournament_sample
        )

        # Verify the tournament was created with correct relations
        assert created_tournament.sport_id == sport.id
        assert created_tournament.season_id == season.id
        assert created_tournament.title == tournament_sample.title


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
