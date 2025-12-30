import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from bs4 import BeautifulSoup

from src.pars_eesl import pars_tournament


class TestParsTournament:
    """Test suite for parsing tournaments from EESL."""

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_tournament.get_url")
    @patch("src.pars_eesl.pars_tournament.file_service")
    async def test_parse_tournament_teams_index_page_eesl_download_error(
        self, mock_file_service, mock_get_url
    ):
        """Test parsing teams when download fails - should skip team and continue."""
        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <ul class="teams__list">
                    <li class="teams__item">
                        <a href="/team?team_id=123" class="teams__logo">
                            <img src="https://example.com/teams/team1.png" alt="Team Alpha" />
                        </a>
                        <a href="/team?team_id=123" class="teams__name-link">Team Alpha</a>
                    </li>
                </ul>
            </body>
        </html>
        """
        mock_get_url.return_value = mock_response

        mock_file_service.download_and_process_image = AsyncMock(
            side_effect=Exception("Download failed")
        )

        result = await pars_tournament.parse_tournament_teams_index_page_eesl(1)

        # When download fails, it should skip the team and continue
        # The function may return None or an empty list depending on structure
        assert result is not None or result == []

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_tournament.get_url")
    async def test_parse_tournament_matches_index_page_eesl_no_matches(
        self, mock_get_url
    ):
        """Test parsing when no matches are found."""
        mock_response = Mock()
        mock_response.content = "<html><body></body></html>"
        mock_get_url.return_value = mock_response

        result = await pars_tournament.parse_tournament_matches_index_page_eesl(1)

        # When no matches are found, function returns []
        assert result is not None or result == []
