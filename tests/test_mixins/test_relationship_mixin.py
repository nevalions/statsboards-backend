import pytest

from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import SeasonFactorySample, SportFactorySample, TournamentFactory



class TestRelationshipMixin:
    """Test suite for RelationshipMixin methods."""

    @pytest.mark.asyncio
    async def test_get_related_items_with_property(self, test_db):
        """Test get_related_items with valid property."""
        tournament_service = TournamentServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)

        sport = await sport_service.create(SportFactorySample.build())
        season = await season_service.create(SeasonFactorySample.build())

        tournament_data = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id
        )
        tournament = await tournament_service.create(tournament_data)

        result = await tournament_service.get_related_items(
            tournament.id, related_property="sport"
        )
        assert result is not None
        assert result.sport_id == sport.id

    @pytest.mark.asyncio
    async def test_get_related_items_without_property(self, test_db):
        """Test get_related_items without related_property (returns base model)."""
        tournament_service = TournamentServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)

        sport = await sport_service.create(SportFactorySample.build())
        season = await season_service.create(SeasonFactorySample.build())

        tournament_data = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id
        )
        tournament = await tournament_service.create(tournament_data)

        result = await tournament_service.get_related_items(tournament.id)
        assert result is not None
        assert result.id == tournament.id

    @pytest.mark.asyncio
    async def test_get_related_items_not_found(self, test_db):
        """Test get_related_items with non-existent ID."""
        tournament_service = TournamentServiceDB(test_db)
        result = await tournament_service.get_related_items(
            99999, related_property="sport"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_related_item_level_one_by_id_single_object(self, test_db, sport):
        """Test get_related_item_level_one_by_id for single-object relationship."""
        sport_service = SportServiceDB(test_db)
        result = await sport_service.get_related_item_level_one_by_id(
            sport.id, "tournaments"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_related_item_level_one_by_id_not_found(self, test_db):
        """Test get_related_item_level_one_by_id with non-existent ID."""
        sport_service = SportServiceDB(test_db)
        result = await sport_service.get_related_item_level_one_by_id(
            99999, "tournaments"
        )
        assert result is None or result == []

    @pytest.mark.asyncio
    async def test_get_nested_related_item_by_id(self, test_db):
        """Test get_nested_related_item_by_id."""
        tournament_service = TournamentServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)

        sport = await sport_service.create(SportFactorySample.build())
        season = await season_service.create(SeasonFactorySample.build())

        tournament_data = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id
        )
        tournament = await tournament_service.create(tournament_data)

        result = await tournament_service.get_nested_related_item_by_id(
            tournament.id,
            season_service,
            "season",
            "tournaments",
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_related_item_level_one_by_key_and_value(self, test_db):
        """Test get_related_item_level_one_by_key_and_value."""
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        result = await season_service.get_related_item_level_one_by_key_and_value(
            "id", season.id, "tournaments"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_related_items_by_two(self, test_db):
        """Test get_related_items_by_two for two-level relationships."""
        season_service = SeasonServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)

        sport = await sport_service.create(SportFactorySample.build())
        season = await season_service.create(SeasonFactorySample.build())

        tournament_data = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id
        )
        await tournament_service.create(tournament_data)

        result = await season_service.get_related_items_by_two(
            "id",
            season.id,
            tournament_service.model,
            "tournaments",
            "sport",
        )
        assert result is not None
