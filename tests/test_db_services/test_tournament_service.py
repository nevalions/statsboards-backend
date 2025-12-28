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
    sport_sample,
    season_sample,
)
from tests.testhelpers import (
    assert_tournament_equal,
    assert_http_exception_on_create,
    assert_tournaments_equal,
)


@pytest.fixture(scope="function")
def tournament_sample(sport_sample, season_sample) -> TournamentSchemaCreate:
    return TournamentFactory.build(
        sport_id=sport_sample.id,
        season_id=season_sample.id,
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
        from src.tournaments.schemas import TournamentSchemaCreate
        invalid_tournament_sample = TournamentSchemaCreate.model_construct(
            sport_id=None,
            season_id=tournament_sample.season_id,
        )

        with pytest.raises(HTTPException) as exc_info:
            await test_tournament_service.create_tournament(invalid_tournament_sample)

        assert_http_exception_on_create(exc_info)

    async def test_create_tournament_without_season_id(
        self,
        test_tournament_service: TournamentServiceDB,
        tournament_sample: TournamentSchemaCreate,
    ):
        """Test that a tournament cannot be created without a season_id."""
        invalid_tournament_sample = TournamentSchemaCreate.model_construct(
            sport_id=tournament_sample.sport_id,
            season_id=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            await test_tournament_service.create_tournament(invalid_tournament_sample)

        assert_http_exception_on_create(exc_info)

    async def test_create_tournament_without_the_same_eesl_id(
        self,
        test_tournament_service: TournamentServiceDB,
        tournament_sample: TournamentSchemaCreate,
    ):
        """Test that a tournament cannot be created with same tournament_eesl_id."""
        invalid_tournament_sample = TournamentSchemaCreate.model_construct(
            tournament_eesl_id=tournament_sample.tournament_eesl_id,
        )

        with pytest.raises(HTTPException) as exc_info:
            await test_tournament_service.create_tournament(invalid_tournament_sample)

        assert_http_exception_on_create(exc_info)

    async def test_get_tournament_with_eesl_id(
        self,
        test_tournament_service: TournamentServiceDB,
        tournament: TournamentSchemaCreate,
        season: SeasonSchemaCreate,
        sport: SportSchemaCreate,
    ):
        """Test that a tournament can be retrieved using its eesl_id."""
        retrieved_tournament = await test_tournament_service.get_tournament_by_eesl_id(
            tournament.tournament_eesl_id
        )
        assert_tournament_equal(tournament, retrieved_tournament, season, sport)
