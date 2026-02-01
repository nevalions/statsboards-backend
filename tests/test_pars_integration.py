import aiohttp
import pytest

from src.pars_eesl import pars_all_players_from_eesl, pars_season, pars_tournament


async def is_website_reachable(url: str, timeout: int = 5) -> bool:
    """Check if website is reachable."""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.head(url, allow_redirects=True) as response:
                return response.status < 500
    except Exception:
        return False


@pytest.mark.integration
class TestParsAllPlayersIntegration:
    """Integration tests for parsing players from real EESL website."""

    @pytest.mark.asyncio
    async def test_collect_player_full_data_eesl_real(self, test_uploads_path):
        """Test collecting full player data from real website."""
        if not await is_website_reachable("https://fafr.su"):
            pytest.skip("EESL website not reachable, skipping integration test")

        player_eesl_id = 1812

        result = await pars_all_players_from_eesl.collect_player_full_data_eesl(player_eesl_id)

        assert result is not None
        assert "person" in result
        assert "player" in result
        assert result["person"]["person_eesl_id"] == player_eesl_id
        assert result["person"]["first_name"] is not None
        assert result["person"]["second_name"] is not None
        assert result["player"]["player_eesl_id"] == player_eesl_id

        # Note: Files are downloaded to production directory during tests
        # The monkeypatch approach doesn't work due to module import timing
        print("\nTest completed. Player data parsed successfully.")
        print(f"First name: {result['person']['first_name']}")
        print(f"Last name: {result['person']['second_name']}")
        print(f"Photo icon URL: {result['person']['person_photo_icon_url']}")

    @pytest.mark.asyncio
    async def test_collect_players_dob_from_all_eesl_real(self, test_uploads_path):
        """Test collecting player DOB from real website."""
        if not await is_website_reachable("https://fafr.su"):
            pytest.skip("EESL website not reachable, skipping integration test")

        player_eesl_id = 1812

        result = await pars_all_players_from_eesl.collect_players_dob_from_all_eesl(player_eesl_id)

        assert result is not None
        assert result.year > 1990

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_parse_all_players_from_eesl_index_page_eesl_real_limit_2(
        self, test_uploads_path
    ):
        """Test parsing limited number of players from real website."""
        if not await is_website_reachable("https://fafr.su"):
            pytest.skip("EESL website not reachable, skipping integration test")

        result = await pars_all_players_from_eesl.parse_all_players_from_eesl_index_page_eesl(
            start_page=0, limit=2, season_id=8
        )

        assert result is not None
        assert len(result) <= 2
        if len(result) > 0:
            assert "person" in result[0]
            assert "player" in result[0]


@pytest.mark.integration
class TestParsTournamentIntegration:
    """Integration tests for parsing tournaments from real EESL website."""

    @pytest.mark.asyncio
    async def test_parse_tournament_teams_index_page_eesl_real(self, test_uploads_path):
        """Test parsing teams from real tournament website."""
        if not await is_website_reachable("https://fafr.su"):
            pytest.skip("EESL website not reachable, skipping integration test")

        tournament_eesl_id = 28

        result = await pars_tournament.parse_tournament_teams_index_page_eesl(tournament_eesl_id)

        assert result is not None
        assert isinstance(result, list)
        if len(result) > 0:
            team = result[0]
            assert "team_eesl_id" in team
            assert "title" in team
            assert "team_logo_url" in team


@pytest.mark.integration
class TestParsSeasonIntegration:
    """Integration tests for parsing seasons from real EESL website."""

    @pytest.mark.asyncio
    async def test_parse_season_index_page_eesl_real(self, test_uploads_path):
        """Test parsing season from real website."""
        if not await is_website_reachable("https://fafr.su"):
            pytest.skip("EESL website not reachable, skipping integration test")

        season_id = 8

        result = await pars_season.parse_season_index_page_eesl(season_id)

        assert result is not None
        assert isinstance(result, list)
        if len(result) > 0:
            tournament = result[0]
            assert "tournament_eesl_id" in tournament
            assert "title" in tournament
            assert "tournament_logo_url" in tournament
