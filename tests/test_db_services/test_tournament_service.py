import pytest

from src.seasons.schemas import SeasonSchemaCreate
from src.sports.schemas import SportSchemaCreate
from src.tournaments.db_services import TournamentServiceDB
from src.tournaments.schemas import TournamentSchemaBase
from tests.factories import TournamentFactory
from tests.fixtures import (
    test_tournament_service,
    test_sport_service,
    test_season_service,
    tournament,
    sport,
    season,
)
from tests.test_data import TestData


@pytest.fixture(scope="function")
def tournament_sample(sport, season):
    return TournamentFactory.build(sport_id=sport.id, season_id=season.id)


@pytest.mark.asyncio
class TestTournamentServiceDB:
    async def test_create_tournament_with_relations(
        self,
        test_tournament_service: TournamentServiceDB,
        sport: SportSchemaCreate,
        season: SeasonSchemaCreate,
        tournament_sample,
    ):
        """Test creating a tournament with related sport and season."""
        created_tournament: TournamentSchemaBase = (
            await test_tournament_service.create_tournament(tournament_sample)
        )

        assert created_tournament.sport_id == sport.id
        assert created_tournament.season_id == season.id
        assert created_tournament.title == tournament_sample.title
        assert created_tournament.description == tournament_sample.description
        assert (
            created_tournament.tournament_logo_url
            == tournament_sample.tournament_logo_url
        )
        assert (
            created_tournament.tournament_logo_icon_url
            == tournament_sample.tournament_logo_icon_url
        )
        assert (
            created_tournament.tournament_logo_web_url
            == tournament_sample.tournament_logo_web_url
        )
        assert created_tournament.sponsor_line_id == tournament_sample.sponsor_line_id
        assert created_tournament.main_sponsor_id == tournament_sample.main_sponsor_id
        assert sport.title == TestData.get_sport_data().title
        assert season.year == TestData.get_season_data().year
