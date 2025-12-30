import pytest
import pytest_asyncio
from fastapi import HTTPException

from src.core.models.base import Database
from src.matches.db_services import MatchServiceDB
from src.matches.schemas import MatchSchemaCreate, MatchSchemaUpdate
from src.teams.db_services import TeamServiceDB
from src.teams.schemas import TeamSchemaCreate
from src.tournaments.db_services import TournamentServiceDB
from src.tournaments.schemas import TournamentSchemaCreate
from src.seasons.db_services import SeasonServiceDB
from src.seasons.schemas import SeasonSchemaCreate
from src.sports.db_services import SportServiceDB
from src.sports.schemas import SportSchemaCreate
from tests.factories import (
    MatchFactory,
    TeamFactory,
    TournamentFactory,
    SportFactorySample,
    SeasonFactorySample,
)
from src.logging_config import setup_logging
from datetime import datetime

setup_logging()


@pytest.fixture(scope="function")
def sport(test_db: Database):
    return SportFactorySample.build()


@pytest.fixture(scope="function")
def season(test_db: Database):
    return SeasonFactorySample.build(year=2024)


@pytest_asyncio.fixture(scope="function")
async def tournament_data(
    test_db: Database, sport: SportSchemaCreate, season: SeasonSchemaCreate
):
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

    team1 = TeamFactory.build(
        sport_id=created_sport.id, team_eesl_id=801, title="Team A"
    )
    team2 = TeamFactory.build(
        sport_id=created_sport.id, team_eesl_id=802, title="Team B"
    )

    created_team1 = await team_service.create_or_update_team(team1)
    created_team2 = await team_service.create_or_update_team(team2)

    return created_team1, created_team2


@pytest.mark.asyncio
class TestMatchServiceDBCreateOrUpdate:
    """Test create_or_update_match functionality."""

    async def test_create_match_with_eesl_id(
        self, test_db: Database, tournament_data: TournamentSchemaCreate, teams_data
    ):
        """Test creating a match with eesl_id."""
        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create_or_update_tournament(
            tournament_data
        )

        team_a, team_b = teams_data

        match_service = MatchServiceDB(test_db)
        match_data = MatchFactory.build(
            match_eesl_id=100,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        result = await match_service.create_or_update_match(match_data)

        assert result is not None
        assert result.id is not None
        assert result.match_eesl_id == 100
        assert result.tournament_id == created_tournament.id

    async def test_create_match_without_eesl_id(
        self, test_db: Database, tournament_data: TournamentSchemaCreate, teams_data
    ):
        """Test creating a match without eesl_id."""
        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create_or_update_tournament(
            tournament_data
        )

        team_a, team_b = teams_data

        match_service = MatchServiceDB(test_db)
        match_data = MatchFactory.build(
            match_eesl_id=None,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        result = await match_service.create_or_update_match(match_data)

        assert result is not None
        assert result.id is not None
        assert result.match_eesl_id is None

    async def test_update_existing_match_by_eesl_id(
        self, test_db: Database, tournament_data: TournamentSchemaCreate, teams_data
    ):
        """Test updating an existing match by eesl_id."""
        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create_or_update_tournament(
            tournament_data
        )

        team_a, team_b = teams_data

        match_service = MatchServiceDB(test_db)

        match_data = MatchFactory.build(
            match_eesl_id=200,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            week=1,
            match_date=datetime.now(),
        )
        created = await match_service.create_or_update_match(match_data)

        update_data = MatchSchemaUpdate(match_eesl_id=200, week=2)

        updated = await match_service.create_or_update_match(update_data)

        assert updated.id == created.id
        assert updated.week == 2

    async def test_create_multiple_matches(
        self, test_db: Database, tournament_data: TournamentSchemaCreate, teams_data
    ):
        """Test creating multiple matches."""
        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create_or_update_tournament(
            tournament_data
        )

        team_a, team_b = teams_data

        match_service = MatchServiceDB(test_db)

        match1_data = MatchFactory.build(
            match_eesl_id=301,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )
        match2_data = MatchFactory.build(
            match_eesl_id=302,
            tournament_id=created_tournament.id,
            team_a_id=team_b.id,
            team_b_id=team_a.id,
            match_date=datetime.now(),
        )

        match1 = await match_service.create_or_update_match(match1_data)
        match2 = await match_service.create_or_update_match(match2_data)

        assert match1.match_eesl_id == 301
        assert match2.match_eesl_id == 302
        assert match1.id != match2.id

    async def test_get_match_by_eesl_id(
        self, test_db: Database, tournament_data: TournamentSchemaCreate, teams_data
    ):
        """Test retrieving match by eesl_id."""
        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create_or_update_tournament(
            tournament_data
        )

        team_a, team_b = teams_data

        match_service = MatchServiceDB(test_db)

        match_data = MatchFactory.build(
            match_eesl_id=400,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )
        created = await match_service.create_or_update_match(match_data)

        retrieved = await match_service.get_match_by_eesl_id(400)

        assert retrieved is not None
        assert retrieved.id == created.id
