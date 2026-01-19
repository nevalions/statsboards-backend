import pytest
from fastapi import HTTPException

from src.core.models import SponsorSponsorLineDB
from src.seasons.db_services import SeasonServiceDB
from src.sponsor_lines.db_services import SponsorLineServiceDB
from src.sponsors.db_services import SponsorServiceDB
from src.sports.db_services import SportServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import (
    SeasonFactorySample,
    SponsorFactory,
    SponsorLineFactory,
    SportFactorySample,
    TournamentFactory,
)


class TestRelationshipMixin:
    """Test suite for RelationshipMixin methods."""

    @pytest.mark.asyncio
    async def test_find_relation_existing(self, test_db):
        """Test find_relation with existing relation."""
        sponsor_service = SponsorServiceDB(test_db)
        sponsor_line_service = SponsorLineServiceDB(test_db)

        sponsor = await sponsor_service.create(SponsorFactory.build())
        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        await sponsor_service.create_m2m_relation(
            parent_model=type(sponsor),
            child_model=type(sponsor_line),
            secondary_table=SponsorSponsorLineDB,
            parent_id=sponsor.id,
            child_id=sponsor_line.id,
            parent_id_name="sponsor_id",
            child_id_name="sponsor_line_id",
            child_relation="sponsor_lines",
        )

        result = await sponsor_service.find_relation(
            secondary_table=SponsorSponsorLineDB,
            fk_item_one=sponsor.id,
            fk_item_two=sponsor_line.id,
            field_name_one="sponsor_id",
            field_name_two="sponsor_line_id",
        )

        assert result is not None
        assert result.sponsor_id == sponsor.id
        assert result.sponsor_line_id == sponsor_line.id

    @pytest.mark.asyncio
    async def test_find_relation_not_existing(self, test_db):
        """Test find_relation with non-existing relation."""
        sponsor_service = SponsorServiceDB(test_db)

        result = await sponsor_service.find_relation(
            secondary_table=SponsorSponsorLineDB,
            fk_item_one=999,
            fk_item_two=999,
            field_name_one="sponsor_id",
            field_name_two="sponsor_line_id",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_is_relation_exist_true(self, test_db):
        """Test is_relation_exist when relation exists."""
        sponsor_service = SponsorServiceDB(test_db)
        sponsor_line_service = SponsorLineServiceDB(test_db)

        sponsor = await sponsor_service.create(SponsorFactory.build())
        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        await sponsor_service.create_m2m_relation(
            parent_model=type(sponsor),
            child_model=type(sponsor_line),
            secondary_table=SponsorSponsorLineDB,
            parent_id=sponsor.id,
            child_id=sponsor_line.id,
            parent_id_name="sponsor_id",
            child_id_name="sponsor_line_id",
            child_relation="sponsor_lines",
        )

        result = await sponsor_service.is_relation_exist(
            secondary_table=SponsorSponsorLineDB,
            fk_item_one=sponsor.id,
            fk_item_two=sponsor_line.id,
            field_name_one="sponsor_id",
            field_name_two="sponsor_line_id",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_is_relation_exist_false(self, test_db):
        """Test is_relation_exist when relation does not exist."""
        sponsor_service = SponsorServiceDB(test_db)

        result = await sponsor_service.is_relation_exist(
            secondary_table=SponsorSponsorLineDB,
            fk_item_one=999,
            fk_item_two=999,
            field_name_one="sponsor_id",
            field_name_two="sponsor_line_id",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_create_m2m_relation_success(self, test_db):
        """Test create_m2m_relation successful creation."""
        sponsor_service = SponsorServiceDB(test_db)
        sponsor_line_service = SponsorLineServiceDB(test_db)

        sponsor = await sponsor_service.create(SponsorFactory.build())
        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        result = await sponsor_service.create_m2m_relation(
            parent_model=type(sponsor),
            child_model=type(sponsor_line),
            secondary_table=SponsorSponsorLineDB,
            parent_id=sponsor.id,
            child_id=sponsor_line.id,
            parent_id_name="sponsor_id",
            child_id_name="sponsor_line_id",
            child_relation="sponsor_lines",
        )

        assert result is not None
        assert len(result) == 1
        assert result[0].id == sponsor_line.id

    @pytest.mark.asyncio
    async def test_create_m2m_relation_already_exists(self, test_db):
        """Test create_m2m_relation when relation already exists."""
        sponsor_service = SponsorServiceDB(test_db)
        sponsor_line_service = SponsorLineServiceDB(test_db)

        sponsor = await sponsor_service.create(SponsorFactory.build())
        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        await sponsor_service.create_m2m_relation(
            parent_model=type(sponsor),
            child_model=type(sponsor_line),
            secondary_table=SponsorSponsorLineDB,
            parent_id=sponsor.id,
            child_id=sponsor_line.id,
            parent_id_name="sponsor_id",
            child_id_name="sponsor_line_id",
            child_relation="sponsor_lines",
        )

        with pytest.raises(HTTPException) as exc_info:
            await sponsor_service.create_m2m_relation(
                parent_model=type(sponsor),
                child_model=type(sponsor_line),
                secondary_table=SponsorSponsorLineDB,
                parent_id=sponsor.id,
                child_id=sponsor_line.id,
                parent_id_name="sponsor_id",
                child_id_name="sponsor_line_id",
                child_relation="sponsor_lines",
            )

        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_m2m_relation_parent_not_found(self, test_db):
        """Test create_m2m_relation when parent does not exist."""
        from src.core.models import SponsorDB

        sponsor_service = SponsorServiceDB(test_db)
        sponsor_line_service = SponsorLineServiceDB(test_db)

        sponsor_line = await sponsor_line_service.create(SponsorLineFactory.build())

        with pytest.raises(HTTPException) as exc_info:
            await sponsor_service.create_m2m_relation(
                parent_model=SponsorDB,
                child_model=type(sponsor_line),
                secondary_table=SponsorSponsorLineDB,
                parent_id=999,
                child_id=sponsor_line.id,
                parent_id_name="sponsor_id",
                child_id_name="sponsor_line_id",
                child_relation="sponsor_lines",
            )

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_m2m_relation_child_not_found(self, test_db):
        """Test create_m2m_relation when child does not exist."""
        from src.core.models import SponsorLineDB

        sponsor_service = SponsorServiceDB(test_db)

        sponsor = await sponsor_service.create(SponsorFactory.build())

        with pytest.raises(HTTPException) as exc_info:
            await sponsor_service.create_m2m_relation(
                parent_model=type(sponsor),
                child_model=SponsorLineDB,
                secondary_table=SponsorSponsorLineDB,
                parent_id=sponsor.id,
                child_id=999,
                parent_id_name="sponsor_id",
                child_id_name="sponsor_line_id",
                child_relation="sponsor_lines",
            )

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_related_items_with_property(self, test_db):
        """Test get_related_items with valid property."""
        tournament_service = TournamentServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)

        sport = await sport_service.create(SportFactorySample.build())
        season = await season_service.create(SeasonFactorySample.build())

        tournament_data = TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        tournament = await tournament_service.create(tournament_data)

        result = await tournament_service.get_related_items(tournament.id, related_property="sport")
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

        tournament_data = TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        tournament = await tournament_service.create(tournament_data)

        result = await tournament_service.get_related_items(tournament.id)
        assert result is not None
        assert result.id == tournament.id

    @pytest.mark.asyncio
    async def test_get_related_items_not_found(self, test_db):
        """Test get_related_items with non-existent ID."""
        tournament_service = TournamentServiceDB(test_db)
        result = await tournament_service.get_related_items(99999, related_property="sport")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_related_item_level_one_by_id_single_object(self, test_db, sport):
        """Test get_related_item_level_one_by_id for single-object relationship."""
        sport_service = SportServiceDB(test_db)
        result = await sport_service.get_related_item_level_one_by_id(sport.id, "tournaments")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_related_item_level_one_by_id_not_found(self, test_db):
        """Test get_related_item_level_one_by_id with non-existent ID."""
        sport_service = SportServiceDB(test_db)
        result = await sport_service.get_related_item_level_one_by_id(99999, "tournaments")
        assert result is None or result == []

    @pytest.mark.asyncio
    async def test_get_nested_related_item_by_id(self, test_db):
        """Test get_nested_related_item_by_id."""
        tournament_service = TournamentServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)

        sport = await sport_service.create(SportFactorySample.build())
        season = await season_service.create(SeasonFactorySample.build())

        tournament_data = TournamentFactory.build(sport_id=sport.id, season_id=season.id)
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

        tournament_data = TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        await tournament_service.create(tournament_data)

        result = await season_service.get_related_items_by_two(
            "id",
            season.id,
            tournament_service.model,
            "tournaments",
            "sport",
        )
        assert result is not None
