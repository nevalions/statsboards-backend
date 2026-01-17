import pytest
from fastapi import HTTPException

from src.seasons.schemas import SeasonSchemaCreate, SeasonSchemaUpdate
from tests.factories import SeasonFactorySample
from tests.test_data import TestData
from tests.testhelpers import (
    assert_http_exception_on_create,
    assert_http_exception_on_delete,
    assert_http_exception_on_update,
    assert_season_equal,
    assert_tournament_equal,
    assert_tournaments_equal,
)


@pytest.fixture(scope="function")
def season_sample():
    return SeasonFactorySample.build()


# Fixture to provide updated season data for update operation
@pytest.fixture(scope="function")
def updated_season_data():
    """Fixture to provide updated season data."""
    return TestData.get_season_data_for_update()


# Test class for SeasonServiceDB
@pytest.mark.asyncio
class TestSeasonServiceDB:
    async def test_create_season_success(
        self,
        test_season_service,
        season_sample,
    ):
        """Test successful season creation."""
        created_season: SeasonSchemaCreate = await test_season_service.create(season_sample)
        assert_season_equal(season_sample, created_season)

    async def test_delete_season_success(
        self,
        test_season_service,
        season,
    ):
        """Test successful season deletion"""
        assert season is not None
        await test_season_service.delete(season.id)
        got_season = await test_season_service.get_by_id(season.id)
        assert got_season is None

    async def test_delete_season_fail(
        self,
        test_season_service,
        season,
    ):
        """Test successful season deletion"""
        with pytest.raises(HTTPException) as exc_info:
            await test_season_service.delete(season.id + 1)

        assert_http_exception_on_delete(exc_info)
        assert season is not None
        got_season = await test_season_service.get_by_id(season.id)
        assert got_season is not None

    async def test_get_season_by_id_success(
        self,
        test_season_service,
        season,
    ):
        """Test successful retrieval of a season."""
        got_season = await test_season_service.get_by_id(season.id)
        assert_season_equal(season, got_season)

    async def test_get_season_by_id_fail(
        self,
        test_season_service,
        season_sample,
    ):
        """Test season not found by year."""
        await test_season_service.create(season_sample)
        got_season = await test_season_service.get_by_id(0)

        assert got_season is None

    async def test_get_season_by_year_success(
        self,
        test_season_service,
        season,
        season_sample,
    ):
        """Test successful retrieval of a season."""
        got_season = await test_season_service.get_season_by_year(season.year)
        assert_season_equal(season, got_season)

    async def test_get_season_by_year_not_found(
        self,
        test_season_service,
        season_sample,
    ):
        """Test season not found by year."""
        got_season = await test_season_service.get_season_by_year(1)

        assert got_season is None

    async def test_update_season_success(
        self,
        test_season_service,
        season,
        updated_season_data,
    ):
        """Test successful season update."""
        updated_season = await test_season_service.update(
            item_id=season.id, item=updated_season_data
        )
        assert updated_season is not None
        assert updated_season.year == updated_season_data.year
        assert updated_season.description == updated_season_data.description
        assert updated_season.id == season.id
        assert updated_season.year != season.year
        assert updated_season.year == TestData.get_season_data_for_update().year

        # Reset season back to its original state
        reset_season_data = SeasonSchemaUpdate(year=season.year, description=season.description)
        await test_season_service.update(item_id=season.id, item=reset_season_data)
        reset_season = await test_season_service.get_season_by_year(season.year)
        assert_season_equal(season, reset_season)

    async def test_update_season_failure(
        self,
        test_season_service,
        season,
        updated_season_data,
    ):
        """Test failure during season update, expect HTTPException."""
        updated_season_data.year = None
        with pytest.raises(HTTPException) as exc_info:
            await test_season_service.update(
                item_id=season.id,
                item=updated_season_data,
            )

        assert_http_exception_on_update(exc_info)

    async def test_create_duplicate_season(
        self,
        test_season_service,
        season,
    ):
        """Test attempting to create a duplicate season."""
        duplicate_season = SeasonSchemaCreate(year=season.year, description="Duplicate")
        with pytest.raises(HTTPException) as exc_info:
            await test_season_service.create(duplicate_season)

        assert_http_exception_on_create(exc_info)

    async def test_get_one_tournament_by_year(
        self,
        test_season_service,
        tournament,
        season,
        sport,
    ):
        """Test tournaments for the year."""
        season_id = tournament.season_id
        got_season = await test_season_service.get_by_id(season_id)
        got_tournaments = await test_season_service.get_tournaments_by_year(got_season.year)

        assert len(got_tournaments) == 1
        assert_tournament_equal(tournament, got_tournaments[0], season, sport)

    async def test_get_tournaments_by_year(
        self,
        test_season_service,
        tournaments,
    ):
        """Test retrieving tournaments for a given year."""
        season_id = tournaments[0].season_id
        got_season = await test_season_service.get_by_id(season_id)

        fetched_tournaments = await test_season_service.get_tournaments_by_year(got_season.year)

        assert_tournaments_equal(tournaments, fetched_tournaments)

    async def test_get_tournaments_by_year_and_sport(
        self,
        test_season_service,
        tournaments,
    ):
        """Test retrieving tournaments for a given year and sport."""
        season_id = tournaments[0].season_id
        sport_id = tournaments[0].sport_id
        got_season = await test_season_service.get_by_id(season_id)

        fetched_tournaments = await test_season_service.get_tournaments_by_year_and_sport(
            year=got_season.year,
            sport_id=sport_id,
        )
        assert_tournaments_equal(tournaments, fetched_tournaments)

    async def test_get_tournaments_by_season_id_and_sport_id(
        self,
        test_season_service,
        tournaments,
    ):
        """Test retrieving tournaments for a given year and sport."""
        season_id = tournaments[0].season_id
        sport_id = tournaments[0].sport_id

        fetched_tournaments = await test_season_service.get_tournaments_by_season_and_sport_ids(
            season_id=season_id,
            sport_id=sport_id,
        )
        assert_tournaments_equal(tournaments, fetched_tournaments)

    async def test_search_seasons_with_pagination_success(
        self,
        test_season_service,
    ):
        """Test search seasons with pagination returns correct results."""
        for i in range(5):
            await test_season_service.create(SeasonFactorySample.build(year=2020 + i))

        result = await test_season_service.search_seasons_with_pagination(
            skip=0,
            limit=2,
            order_by="year",
            order_by_two="id",
            ascending=True,
        )

        assert result is not None
        assert len(result.data) == 2
        assert result.metadata.page == 1
        assert result.metadata.items_per_page == 2
        assert result.metadata.total_items >= 5
        assert result.metadata.total_pages >= 3
        assert result.metadata.has_next is True
        assert result.metadata.has_previous is False

    async def test_search_seasons_with_pagination_search_query(
        self,
        test_season_service,
    ):
        """Test search seasons with query filters correctly."""
        await test_season_service.create(
            SeasonFactorySample.build(year=2025, description="Season Alpha")
        )
        await test_season_service.create(
            SeasonFactorySample.build(year=2026, description="Season Beta")
        )
        await test_season_service.create(
            SeasonFactorySample.build(year=2027, description="Season Gamma")
        )

        result = await test_season_service.search_seasons_with_pagination(
            search_query="Season",
            skip=0,
            limit=10,
            order_by="year",
            order_by_two="id",
            ascending=True,
        )

        assert result is not None
        assert len(result.data) == 3
        assert result.metadata.total_items == 3

    async def test_search_seasons_with_pagination_empty_search(
        self,
        test_season_service,
    ):
        """Test empty search query returns all seasons."""
        await test_season_service.create(SeasonFactorySample.build(year=2023))
        await test_season_service.create(SeasonFactorySample.build(year=2024))

        result = await test_season_service.search_seasons_with_pagination(
            search_query=None,
            skip=0,
            limit=10,
            order_by="year",
            order_by_two="id",
            ascending=True,
        )

        assert result is not None
        assert len(result.data) >= 2

    async def test_search_seasons_with_pagination_ordering(
        self,
        test_season_service,
    ):
        """Test ordering works correctly."""
        await test_season_service.create(SeasonFactorySample.build(year=2023))
        await test_season_service.create(SeasonFactorySample.build(year=2024))
        await test_season_service.create(SeasonFactorySample.build(year=2026))

        result_asc = await test_season_service.search_seasons_with_pagination(
            search_query=None,
            skip=0,
            limit=10,
            order_by="year",
            order_by_two="id",
            ascending=True,
        )

        result_desc = await test_season_service.search_seasons_with_pagination(
            search_query=None,
            skip=0,
            limit=10,
            order_by="year",
            order_by_two="id",
            ascending=False,
        )

        assert result_asc is not None
        assert result_desc is not None
        years_asc = [s.year for s in result_asc.data]
        years_desc = [s.year for s in result_desc.data]
        assert years_asc == sorted(years_asc)
        assert years_desc == sorted(years_desc, reverse=True)

    async def test_search_seasons_with_pagination_empty_results(
        self,
        test_season_service,
    ):
        """Test empty results returns empty list."""
        result = await test_season_service.search_seasons_with_pagination(
            search_query="NonExistent",
            skip=0,
            limit=10,
            order_by="year",
            order_by_two="id",
            ascending=True,
        )

        assert result is not None
        assert len(result.data) == 0
        assert result.metadata.total_items == 0
        assert result.metadata.total_pages == 0
        assert result.metadata.has_next is False
        assert result.metadata.has_previous is False
