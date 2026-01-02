import pytest
from fastapi import HTTPException

from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from tests.factories import SeasonFactorySample, SportFactorySample


class TestQueryMixin:
    """Test suite for QueryMixin methods."""

    @pytest.mark.asyncio
    async def test_get_item_by_field_value_success(self, test_db, season_db_model):
        """Test successful retrieval of an item by field value."""
        service = SeasonServiceDB(test_db)
        created = await service.create(season_db_model)
        retrieved = await service.get_item_by_field_value(created.year, "year")
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.year == created.year

    @pytest.mark.asyncio
    async def test_get_item_by_field_value_not_found(self, test_db):
        """Test retrieval of non-existent item by field value."""
        service = SeasonServiceDB(test_db)
        retrieved = await service.get_item_by_field_value(99999, "year")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_item_by_field_value_exception_handling(self, test_db):
        """Test exception handling in get_item_by_field_value."""
        service = SeasonServiceDB(test_db)
        with pytest.raises(HTTPException) as exc_info:
            await service.get_item_by_field_value(2025, "invalid_field")
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_update_item_by_eesl_id_success(self, test_db):
        """Test successful update of an item by eesl field."""
        from src.core.models.season import SeasonDB
        from src.seasons.schemas import SeasonSchemaCreate, SeasonSchemaUpdate

        service = SeasonServiceDB(test_db)
        season_data = SeasonSchemaCreate(year=2023, description="Original")
        season_model = SeasonDB(
            year=season_data.year, description=season_data.description
        )
        created = await service.create(season_model)

        update_data = SeasonSchemaUpdate(description="Updated description")
        updated = await service.update_item_by_eesl_id(
            "year", created.year, update_data
        )
        assert updated is not None
        assert updated.description == "Updated description"

    @pytest.mark.asyncio
    async def test_update_item_by_eesl_id_not_found(self, test_db):
        """Test update of non-existent item by eesl field."""
        from src.seasons.schemas import SeasonSchemaUpdate

        service = SeasonServiceDB(test_db)
        update_data = SeasonSchemaUpdate(year=2025, description="Test")
        updated = await service.update_item_by_eesl_id("year", 99999, update_data)
        assert updated is None

    @pytest.mark.asyncio
    async def test_get_count_of_related_items_with_items(self, test_db):
        """Test count of related items when items exist."""
        from src.tournaments.db_services import TournamentServiceDB

        sport_service = SportServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)

        sport = await sport_service.create(SportFactorySample.build())
        season = await season_service.create(SeasonFactorySample.build(year=2024))

        from tests.factories import TournamentFactory

        tournament_data = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id
        )
        tournament = await tournament_service.create(tournament_data)

        count = await tournament_service.get_count_of_items_level_one_by_id(
            tournament.id, "teams"
        )
        assert count >= 0

    @pytest.mark.asyncio
    async def test_get_count_of_related_items_no_items(self, test_db):
        """Test count of related items when no items exist."""
        from src.tournaments.db_services import TournamentServiceDB

        sport_service = SportServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)

        sport = await sport_service.create(SportFactorySample.build())
        season = await season_service.create(SeasonFactorySample.build(year=2024))

        from tests.factories import TournamentFactory

        tournament_data = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id
        )
        tournament = await tournament_service.create(tournament_data)

        count = await tournament_service.get_count_of_items_level_one_by_id(
            tournament.id, "teams"
        )
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_count_of_related_items_invalid_relationship(
        self, test_db, season
    ):
        """Test count with invalid relationship name."""
        service = SeasonServiceDB(test_db)
        count = await service.get_count_of_items_level_one_by_id(
            season.id, "invalid_relationship"
        )
        assert count == 0
