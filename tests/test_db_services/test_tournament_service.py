import pytest
from fastapi import HTTPException

from src.seasons.schemas import SeasonSchemaCreate
from src.sports.schemas import SportSchemaCreate
from src.tournaments.db_services import TournamentServiceDB
from src.tournaments.schemas import TournamentSchemaCreate
from tests.factories import TournamentFactory
from tests.fixtures import (
    test_tournament_service,
    test_sport_service,
    test_season_service,
    tournament,
    sport,
    season,
)
from tests.testhelpers import assert_tournament_equal, assert_http_exception


@pytest.fixture(scope="function")
def tournament_sample(sport, season) -> TournamentSchemaCreate:
    return TournamentFactory.build(
        sport_id=sport.id,
        season_id=season.id,
    )


@pytest.mark.asyncio
class TestTournamentServiceDB:
    async def test_create_tournament_with_relations(
        self,
        test_tournament_service: TournamentServiceDB,
        season: SeasonSchemaCreate,
        sport: SportSchemaCreate,
        tournament_sample: TournamentSchemaCreate,
    ):
        """Test creating a tournament with related sport and season."""
        created_tournament: TournamentSchemaCreate = (
            await test_tournament_service.create_tournament(tournament_sample)
        )
        assert_tournament_equal(
            tournament_sample,
            created_tournament,
            season,
            sport,
        )

    async def test_create_tournament_without_sport_id(
        self,
        test_tournament_service: TournamentServiceDB,
        tournament_sample: TournamentSchemaCreate,
    ):
        """Test that a tournament cannot be created without a sport_id."""
        invalid_tournament_sample = TournamentFactory.build(
            sport_id=None,
            season_id=tournament_sample.season_id,
        )

        with pytest.raises(HTTPException) as exc_info:
            await test_tournament_service.create_tournament(invalid_tournament_sample)

        assert_http_exception(exc_info)

    async def test_create_tournament_without_season_id(
        self,
        test_tournament_service: TournamentServiceDB,
        tournament_sample: TournamentSchemaCreate,
    ):
        """Test that a tournament cannot be created without a season_id."""
        invalid_tournament_sample = TournamentFactory.build(
            sport_id=tournament_sample.sport_id,
            season_id=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            await test_tournament_service.create_tournament(invalid_tournament_sample)

        assert_http_exception(exc_info)

    async def test_create_tournament_without_the_same_eesl_id(
        self,
        test_tournament_service: TournamentServiceDB,
        tournament_sample: TournamentSchemaCreate,
    ):
        """Test that a tournament cannot be created with the same tournament_eesl_id."""
        invalid_tournament_sample: TournamentSchemaCreate = TournamentFactory.build(
            tournament_eesl_id=tournament_sample.tournament_eesl_id,
        )

        with pytest.raises(HTTPException) as exc_info:
            await test_tournament_service.create_tournament(invalid_tournament_sample)

        assert_http_exception(exc_info)
