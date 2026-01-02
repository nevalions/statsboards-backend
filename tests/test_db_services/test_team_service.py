import pytest
from fastapi import HTTPException

from src.core.models.base import Database
from src.sports.db_services import SportServiceDB
from src.sports.schemas import SportSchemaCreate
from src.teams.db_services import TeamServiceDB
from src.teams.schemas import TeamSchemaCreate, TeamSchemaUpdate
from tests.factories import SportFactorySample, TeamFactory


@pytest.fixture(scope="function")
def sport(test_db: Database):
    return SportFactorySample.build()


@pytest.mark.asyncio
class TestTeamServiceDBCreateOrUpdate:
    """Test create_or_update_team functionality."""

    async def test_create_team_with_eesl_id(
        self, test_db: Database, sport: SportSchemaCreate
    ):
        """Test creating a team with eesl_id."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create(sport)

        team_service = TeamServiceDB(test_db)
        team_data = TeamFactory.build(
            sport_id=created_sport.id,
            team_eesl_id=100,
            title="Test Team",
        )

        result = await team_service.create_or_update_team(team_data)

        assert result is not None
        assert result.id is not None
        assert result.team_eesl_id == 100
        assert result.title == "Test Team"

    async def test_create_team_without_eesl_id(
        self, test_db: Database, sport: SportSchemaCreate
    ):
        """Test creating a team without eesl_id."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create(sport)

        team_service = TeamServiceDB(test_db)
        team_data = TeamFactory.build(
            sport_id=created_sport.id,
            team_eesl_id=None,
            title="Team Without EESL",
        )

        result = await team_service.create_or_update_team(team_data)

        assert result is not None
        assert result.id is not None
        assert result.team_eesl_id is None

    async def test_update_existing_team_by_eesl_id(
        self, test_db: Database, sport: SportSchemaCreate
    ):
        """Test updating an existing team by eesl_id."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create(sport)

        team_service = TeamServiceDB(test_db)

        team_data = TeamFactory.build(
            sport_id=created_sport.id,
            team_eesl_id=200,
            title="Original Title",
        )
        created = await team_service.create_or_update_team(team_data)

        update_data = TeamSchemaUpdate(
            team_eesl_id=200,
            title="Updated Title",
            city="Updated City",
        )

        updated = await team_service.create_or_update_team(update_data)

        assert updated.id == created.id
        assert updated.title == "Updated Title"
        assert updated.city == "Updated City"

    async def test_create_multiple_teams_with_same_sport(
        self, test_db: Database, sport: SportSchemaCreate
    ):
        """Test creating multiple teams for the same sport."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create(sport)

        team_service = TeamServiceDB(test_db)

        team1_data = TeamFactory.build(
            sport_id=created_sport.id, team_eesl_id=301, title="Team 1"
        )
        team2_data = TeamFactory.build(
            sport_id=created_sport.id, team_eesl_id=302, title="Team 2"
        )
        team3_data = TeamFactory.build(
            sport_id=created_sport.id, team_eesl_id=303, title="Team 3"
        )

        team1 = await team_service.create_or_update_team(team1_data)
        team2 = await team_service.create_or_update_team(team2_data)
        team3 = await team_service.create_or_update_team(team3_data)

        assert team1.team_eesl_id == 301
        assert team2.team_eesl_id == 302
        assert team3.team_eesl_id == 303
        assert team1.id != team2.id != team3.id

    async def test_update_team_partial_fields(
        self, test_db: Database, sport: SportSchemaCreate
    ):
        """Test updating only some team fields."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create(sport)

        team_service = TeamServiceDB(test_db)

        team_data = TeamFactory.build(
            sport_id=created_sport.id,
            team_eesl_id=400,
            title="Full Title",
            description="Original Description",
        )
        created = await team_service.create_or_update_team(team_data)

        update_data = TeamSchemaUpdate(team_eesl_id=400, description="New Description")

        updated = await team_service.create_or_update_team(update_data)

        assert updated.id == created.id
        assert updated.title == "Full Title"
        assert updated.description == "New Description"

    async def test_error_handling_invalid_data(self, test_db: Database):
        """Test error handling with invalid team data."""
        team_service = TeamServiceDB(test_db)

        invalid_data = TeamSchemaCreate(
            sport_id=99999,
            team_eesl_id=500,
            title="Invalid Team",
        )

        with pytest.raises(HTTPException) as exc_info:
            await team_service.create_or_update_team(invalid_data)

        assert exc_info.value.status_code == 409
