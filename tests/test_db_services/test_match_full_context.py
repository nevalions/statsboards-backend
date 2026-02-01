from datetime import datetime

import pytest
import pytest_asyncio

from src.core.models.base import Database
from src.matches.db_services import MatchServiceDB
from src.seasons.db_services import SeasonServiceDB
from src.seasons.schemas import SeasonSchemaCreate
from src.sports.db_services import SportServiceDB
from src.sports.schemas import SportSchemaCreate
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import (
    MatchFactory,
    SportFactorySample,
    TeamFactory,
    TournamentFactory,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture(scope="function")
def sport(test_db: Database):
    return SportFactorySample.build()


@pytest.fixture(scope="function")
def season(test_db: Database):
    from tests.factories import SeasonFactorySample

    return SeasonFactorySample.build(year=2024)


@pytest_asyncio.fixture(scope="function")
async def tournament_data(test_db: Database, sport: SportSchemaCreate, season: SeasonSchemaCreate):
    sport_service = SportServiceDB(test_db)
    created_sport = await sport_service.create(sport)

    season_service = SeasonServiceDB(test_db)
    created_season = await season_service.create(season)

    return TournamentFactory.build(
        sport_id=created_sport.id, season_id=created_season.id, tournament_eesl_id=900
    )


@pytest_asyncio.fixture(scope="function")
async def teams_data(test_db: Database, sport: SportSchemaCreate):
    sport_service = SportServiceDB(test_db)
    created_sport = await sport_service.create(sport)

    team_service = TeamServiceDB(test_db)

    team1 = TeamFactory.build(sport_id=created_sport.id, team_eesl_id=801, title="Team A")
    team2 = TeamFactory.build(sport_id=created_sport.id, team_eesl_id=802, title="Team B")

    created_team1 = await team_service.create_or_update_team(team1)
    created_team2 = await team_service.create_or_update_team(team2)

    return created_team1, created_team2


class TestMatchServiceDBFullContext:
    """Test get_match_full_context functionality."""

    async def test_get_match_full_context_success(
        self, test_db: Database, tournament_data, teams_data
    ):
        """Test getting match full context with all related data."""
        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create_or_update_tournament(tournament_data)

        match_service = MatchServiceDB(test_db)
        match_data = MatchFactory.build(
            match_eesl_id=100,
            tournament_id=created_tournament.id,
            team_a_id=teams_data[0].id,
            team_b_id=teams_data[1].id,
            match_date=datetime.now(),
        )

        created_match = await match_service.create_or_update_match(match_data)
        assert created_match is not None
        assert created_match.id is not None

        context = await match_service.get_match_full_context(created_match.id)
        assert context is not None
        assert "match" in context
        assert "teams" in context
        assert "sport" in context
        assert "tournament" in context
        assert "players" in context

        assert context["match"]["id"] == created_match.id
        assert context["teams"]["home"]["id"] == teams_data[0].id
        assert context["teams"]["away"]["id"] == teams_data[1].id

    async def test_get_match_full_context_not_found(self, test_db: Database):
        """Test getting match full context for non-existent match."""
        match_service = MatchServiceDB(test_db)
        context = await match_service.get_match_full_context(99999)
        assert context is None
