import pytest
from unittest.mock import Mock, patch, AsyncMock
from bs4 import BeautifulSoup

from src.pars_eesl import pars_season


class TestParsSeason:
    """Test suite for parsing seasons from EESL."""

    @pytest.fixture
    def mock_season_html(self):
        """Mock HTML for season page."""
        return """
        <html>
            <body>
                <ul class="tournaments-archive">
                    <li class="tournaments-archive__item">
                        <a href="/tournament?id=123" class="tournaments-archive__link" title="Season Championship 2024">
                            <img class="tournaments-archive__img" src="https://example.com/tournaments/champ2024_100px.png" />
                        </a>
                    </li>
                </ul>
            </body>
        </html>
        """

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_season.get_url")
    @patch("src.pars_eesl.pars_season.file_service")
    async def test_parse_season_index_page_eesl_success(
        self, mock_file_service, mock_get_url, mock_season_html
    ):
        """Test parsing season successfully."""
        mock_response = Mock()
        mock_response.content = mock_season_html
        mock_get_url.return_value = mock_response

        mock_file_service.download_and_process_image = AsyncMock(
            return_value={
                "image_url": "/static/uploads/tournaments/logos/champ2024.png",
                "image_icon_url": "/static/uploads/tournaments/logos/champ2024_100px.png",
                "image_webview_url": "/static/uploads/tournaments/logos/champ2024_400px.png",
                "image_path": "/static/uploads/tournaments/logos/champ2024.png",
            }
        )

        result = await pars_season.parse_season_index_page_eesl(1)

        assert result is not None
        assert len(result) == 1
        assert result[0]["tournament_eesl_id"] == 123
        assert result[0]["title"] == "season championship 2024"
        assert result[0]["sport_id"] == 1

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_season.get_url")
    async def test_parse_season_index_page_eesl_no_tournaments(self, mock_get_url):
        """Test parsing when no tournaments are found."""
        mock_response = Mock()
        mock_response.content = "<html><body></body></html>"
        mock_get_url.return_value = mock_response

        result = await pars_season.parse_season_index_page_eesl(1)

        assert result is None
