import pytest
from src.core.models.base import BaseServiceDB, Database
from src.core.models.season import SeasonDB
from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import SeasonFactorySample, SportFactorySample, TournamentFactory
from src.logging_config import setup_logging

setup_logging()


class TestBaseServiceDBIntegration:
    """Integration tests for BaseServiceDB combining all mixins."""

    @pytest.mark.asyncio
    async def test_service_initialization(self, test_db):
        """Test that service initializes correctly with all mixins."""
        service = SeasonServiceDB(test_db)
        assert hasattr(service, "create")
        assert hasattr(service, "get_by_id")
        assert hasattr(service, "update")
        assert hasattr(service, "delete")
        assert hasattr(service, "get_item_by_field_value")
        assert hasattr(service, "get_related_items")
        assert hasattr(service, "to_dict")

    @pytest.mark.asyncio
    async def test_full_crud_lifecycle(self, test_db):
        """Test complete CRUD lifecycle using BaseServiceDB."""
        from src.seasons.schemas import SeasonSchemaUpdate

        service = SeasonServiceDB(test_db)

        season_data = SeasonFactorySample.build()
        created = await service.create(season_data)
        assert created.id is not None

        retrieved = await service.get_by_id(created.id)
        assert retrieved.id == created.id

        retrieved_by_year = await service.get_item_by_field_value(
            created.year, "year"
        )
        assert retrieved_by_year.id == created.id

        update_data = SeasonSchemaUpdate(year=created.year + 1)
        updated = await service.update(created.id, update_data)
        assert updated.year == created.year + 1

        deleted = await service.delete(created.id)
        assert deleted.id == created.id

        retrieved_after_delete = await service.get_by_id(created.id)
        assert retrieved_after_delete is None

    @pytest.mark.asyncio
    async def test_relationship_queries(self, test_db):
        """Test relationship queries through BaseServiceDB."""
        sport_service = SportServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)

        sport = await sport_service.create_sport(SportFactorySample.build())
        season = await season_service.create_season(SeasonFactorySample.build())

        tournament_data = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id
        )
        tournament = await tournament_service.create_tournament(tournament_data)

        retrieved_tournament = await tournament_service.get_related_items(
            tournament.id, "sport"
        )
        assert retrieved_tournament.id == sport.id

        retrieved_season = await season_service.get_related_items(
            season.id, "tournaments"
        )
        assert retrieved_season is not None
        if hasattr(retrieved_season, "__len__"):
            assert len(retrieved_season) >= 1
