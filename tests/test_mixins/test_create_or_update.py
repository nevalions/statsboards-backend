import pytest
from fastapi import HTTPException

from src.core.models.base import BaseServiceDB, Database
from src.core.models.season import SeasonDB
from src.seasons.db_services import SeasonServiceDB
from src.seasons.schemas import SeasonSchemaCreate, SeasonSchemaUpdate
from src.sports.db_services import SportServiceDB
from src.sports.schemas import SportSchemaCreate
from src.tournaments.db_services import TournamentServiceDB
from src.tournaments.schemas import TournamentSchemaCreate, TournamentSchemaUpdate
from tests.factories import SeasonFactorySample, SportFactorySample, TournamentFactory
from src.logging_config import setup_logging

setup_logging()


@pytest.mark.asyncio
class TestCreateOrUpdateGeneric:
    """Test generic create_or_update method in BaseServiceDB."""

    async def test_create_when_no_eesl_id(self, test_db: Database):
        """Test creating new record when eesl_id is None."""
        service = SeasonServiceDB(test_db)
        season_data = SeasonFactorySample.build(year=2024)

        result = await service.create_or_update(
            season_data,
            unique_field_name="year",
            unique_field_value=season_data.year,
        )

        assert result is not None
        assert result.id is not None
        assert result.year == 2024

    async def test_create_when_eesl_id_not_in_db(self, test_db: Database):
        """Test creating new record when eesl_id doesn't exist in DB."""
        sport = SportFactorySample.build()
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create(sport)

        season = SeasonFactorySample.build()
        season_service = SeasonServiceDB(test_db)
        created_season = await season_service.create(season)

        tournament_service = TournamentServiceDB(test_db)
        tournament_data = TournamentFactory.build(
            tournament_eesl_id=999,
            sport_id=created_sport.id,
            season_id=created_season.id,
            title="Test Tournament",
        )

        result = await tournament_service.create_or_update(
            tournament_data,
            eesl_field_name="tournament_eesl_id",
        )

        assert result is not None
        assert result.id is not None
        assert result.tournament_eesl_id == 999

    async def test_create_with_valid_data(self, test_db: Database):
        """Test successful creation with all fields."""
        season_service = SeasonServiceDB(test_db)
        season_data = SeasonFactorySample.build(year=2025)
        from src.core.models.season import SeasonDB

        season_model = SeasonDB(
            year=season_data.year, description=season_data.description
        )

        result = await season_service.create_or_update(
            season_data,
            unique_field_name="year",
            unique_field_value=season_data.year,
        )

        assert result.id is not None
        assert result.year == 2025

    async def test_update_when_eesl_id_exists(self, test_db: Database):
        """Test updating existing record by eesl_id."""
        sport = SportFactorySample.build()
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create(sport)

        season = SeasonFactorySample.build()
        season_service = SeasonServiceDB(test_db)
        created_season = await season_service.create(season)

        tournament_service = TournamentServiceDB(test_db)
        tournament_data = TournamentFactory.build(
            tournament_eesl_id=123,
            sport_id=created_sport.id,
            season_id=created_season.id,
            title="Original Title",
        )

        created = await tournament_service.create_or_update(
            tournament_data,
            eesl_field_name="tournament_eesl_id",
        )

        update_data = TournamentSchemaUpdate(
            tournament_eesl_id=123,
            title="Updated Title",
            description="Updated description",
        )

        updated = await tournament_service.create_or_update(
            update_data,
            eesl_field_name="tournament_eesl_id",
        )

        assert updated.id == created.id
        assert updated.title == "Updated Title"
        assert updated.description == "Updated description"

    async def test_update_partial_fields(self, test_db: Database):
        """Test updating only specific fields."""
        season_service = SeasonServiceDB(test_db)
        season_data = SeasonFactorySample.build(year=2030)
        from src.core.models.season import SeasonDB

        season_db_model = SeasonDB(
            year=season_data.year, description=season_data.description
        )
        created = await season_service.create(season_db_model)

        update_data = SeasonSchemaUpdate(year=2031)

        updated = await season_service.create_or_update(
            update_data,
            unique_field_name="year",
            unique_field_value=2030,
        )

        assert updated.id == created.id
        assert updated.year == 2031

    async def test_update_multiple_times(self, test_db: Database):
        """Test sequential updates to the same record."""
        season_service = SeasonServiceDB(test_db)
        season_data = SeasonFactorySample.build(year=2040)
        from src.core.models.season import SeasonDB

        season_db_model = SeasonDB(
            year=season_data.year, description=season_data.description
        )
        created = await season_service.create(season_db_model)

        update1 = SeasonSchemaUpdate(year=2041)
        updated1 = await season_service.create_or_update(
            update1,
            unique_field_name="year",
            unique_field_value=2040,
        )

        update2 = SeasonSchemaUpdate(year=2042)
        updated2 = await season_service.create_or_update(
            update2,
            unique_field_name="year",
            unique_field_value=2041,
        )

        assert updated1.year == 2041
        assert updated2.year == 2042
        assert updated1.id == updated2.id

    async def test_create_or_update_custom_field(self, test_db: Database):
        """Test using custom unique_field_name instead of eesl_id."""
        season_service = SeasonServiceDB(test_db)
        season_data = SeasonFactorySample.build(year=2050)
        from src.core.models.season import SeasonDB

        result = await season_service.create_or_update(
            season_data,
            unique_field_name="year",
            unique_field_value=season_data.year,
        )

        assert result is not None
        assert result.year == 2050

    async def test_custom_field_create(self, test_db: Database):
        """Test create when custom field value doesn't exist."""
        season_service = SeasonServiceDB(test_db)
        season_data = SeasonFactorySample.build(year=2060)

        result = await season_service.create_or_update(
            season_data,
            unique_field_name="year",
            unique_field_value=season_data.year,
        )

        assert result.id is not None
        assert result.year == 2060

    async def test_custom_field_update(self, test_db: Database):
        """Test update when custom field value exists."""
        season_service = SeasonServiceDB(test_db)
        season_data = SeasonFactorySample.build(year=2070)
        from src.core.models.season import SeasonDB

        season_db_model = SeasonDB(
            year=season_data.year, description=season_data.description
        )
        created = await season_service.create(season_db_model)

        retrieved = await season_service.get_by_id(created.id)
        assert retrieved is not None

    async def test_invalid_field_name(self, test_db: Database):
        """Test raising HTTPException when field_name is None."""
        season_service = SeasonServiceDB(test_db)
        season_data = SeasonFactorySample.build(year=2080)

        with pytest.raises(HTTPException) as exc_info:
            await season_service.create_or_update(season_data)

        assert exc_info.value.status_code == 409

    async def test_create_with_model_factory(self, test_db: Database):
        """Test creating with a custom model_factory function."""
        season_service = SeasonServiceDB(test_db)
        season_data = SeasonFactorySample.build(year=2090)
        from src.core.models.season import SeasonDB

        def factory(schema, **kwargs):
            return SeasonDB(year=schema.year)

        result = await season_service.create_or_update(
            season_data,
            unique_field_name="year",
            unique_field_value=season_data.year,
            model_factory=factory,
        )

        assert result is not None
        assert result.year == 2090

    async def test_error_handling_on_invalid_data(self, test_db: Database):
        """Test proper exception handling with invalid data."""
        from src.core.models.season import SeasonDB

        season_service = SeasonServiceDB(test_db)

        season_db_model1 = SeasonDB(year=2099, description="Test Season 1")
        await season_service.create(season_db_model1)

        season_db_model2 = SeasonDB(year=2099, description="Test Season 2")

        with pytest.raises(Exception):
            await season_service.create(season_db_model2)
