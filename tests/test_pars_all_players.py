import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from bs4 import BeautifulSoup

from src.pars_eesl import pars_all_players_from_eesl


class TestParsAllPlayersFromEesl:
    """Test suite for parsing players from EESL."""

    @pytest.fixture
    def mock_player_page_html(self):
        """Mock HTML for a player page."""
        return """
        <html>
            <body>
                <span class="player-promo__value">25 декабря 1990</span>
                <p class="player-promo__name">иванов иван</p>
                <img class="player-promo__img" src="https://example.com/photos/ivanov_ivan.png" />
            </body>
        </html>
        """

    @pytest.fixture
    def mock_players_list_html(self):
        """Mock HTML for players list page."""
        return """
        <html>
            <body>
                <table>
                    <tr class="table__row">
                        <td>
                            <a href="/player?id=123" class="table__player">
                                <span class="table__player-name">петров петр</span>
                            </a>
                            <img class="table__player-img" src="https://example.com/photos/petrov_petr.png" />
                        </td>
                    </tr>
                </table>
                <ul id="players-pagination">
                    <li class="pagination-section__item--arrow pagination-section__item--disabled"></li>
                </ul>
            </body>
        </html>
        """

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_all_players_from_eesl.get_url")
    @patch("src.pars_eesl.pars_all_players_from_eesl.file_service")
    async def test_collect_player_full_data_eesl_success(
        self, mock_file_service, mock_get_url, mock_player_page_html
    ):
        """Test collecting full player data successfully."""
        mock_response = Mock()
        mock_response.content = mock_player_page_html
        mock_get_url.return_value = mock_response

        mock_file_service.download_and_resize_image = AsyncMock()

        result = await pars_all_players_from_eesl.collect_player_full_data_eesl(123)

        assert result is not None
        assert result["person"]["first_name"] == "иван"
        assert result["person"]["second_name"] == "иванов"
        assert result["person"]["person_eesl_id"] == 123
        assert result["player"]["player_eesl_id"] == 123
        assert result["player"]["sport_id"] == "1"

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_all_players_from_eesl.get_url")
    @patch("src.pars_eesl.pars_all_players_from_eesl.file_service")
    async def test_collect_player_full_data_eesl_timeout(
        self, mock_file_service, mock_get_url
    ):
        """Test collecting player data with timeout."""
        mock_get_url.side_effect = asyncio.TimeoutError()

        result = await pars_all_players_from_eesl.collect_player_full_data_eesl(123)

        assert result is None

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_all_players_from_eesl.get_url")
    @patch("src.pars_eesl.pars_all_players_from_eesl.file_service")
    async def test_collect_player_full_data_eesl_download_error(
        self, mock_file_service, mock_get_url, mock_player_page_html
    ):
        """Test collecting player data with download error."""
        mock_response = Mock()
        mock_response.content = mock_player_page_html
        mock_get_url.return_value = mock_response

        mock_file_service.download_and_resize_image = AsyncMock(
            side_effect=Exception("Download failed")
        )

        result = await pars_all_players_from_eesl.collect_player_full_data_eesl(123)

        assert result is not None
        assert result["person"]["person_eesl_id"] == 123
        mock_file_service.download_and_resize_image.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_all_players_from_eesl.get_url")
    @patch("src.pars_eesl.pars_all_players_from_eesl.file_service")
    @patch("src.pars_eesl.pars_all_players_from_eesl.collect_players_dob_from_all_eesl")
    async def test_get_player_from_eesl_participants_success(
        self, mock_collect_dob, mock_file_service, mock_get_url, mock_players_list_html
    ):
        """Test parsing player from participants list successfully."""
        mock_response = Mock()
        mock_response.content = mock_players_list_html
        mock_get_url.return_value = mock_response

        mock_file_service.download_and_resize_image = AsyncMock()
        mock_collect_dob.return_value = datetime(1990, 1, 1)

        players_in_eesl = []
        result = await pars_all_players_from_eesl.get_player_from_eesl_participants(
            players_in_eesl,
            BeautifulSoup(mock_players_list_html, "lxml").find_all(
                "tr", class_="table__row"
            ),
            remaining_limit=10,
        )

        assert result is not False
        assert len(players_in_eesl) == 1
        assert players_in_eesl[0]["person"]["person_eesl_id"] == 123
        assert players_in_eesl[0]["person"]["second_name"] == "петров"
        assert players_in_eesl[0]["person"]["first_name"] == "петр"

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_all_players_from_eesl.get_url")
    @patch("src.pars_eesl.pars_all_players_from_eesl.file_service")
    @patch("src.pars_eesl.pars_all_players_from_eesl.collect_players_dob_from_all_eesl")
    async def test_get_player_from_eesl_participants_download_error(
        self, mock_collect_dob, mock_file_service, mock_get_url, mock_players_list_html
    ):
        """Test parsing player with download error - should skip player and continue."""
        mock_response = Mock()
        mock_response.content = mock_players_list_html
        mock_get_url.return_value = mock_response

        mock_file_service.download_and_resize_image = AsyncMock(
            side_effect=Exception("Download failed")
        )
        mock_collect_dob.return_value = datetime(1990, 1, 1)

        players_in_eesl = []
        result = await pars_all_players_from_eesl.get_player_from_eesl_participants(
            players_in_eesl,
            BeautifulSoup(mock_players_list_html, "lxml").find_all(
                "tr", class_="table__row"
            ),
            remaining_limit=10,
        )

        assert result == []  # Function returns empty list when no players added
        assert len(players_in_eesl) == 0  # No player added due to download error

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_all_players_from_eesl.get_url")
    async def test_parse_all_players_from_eesl_index_page_eesl_no_players(
        self, mock_get_url
    ):
        """Test parsing when no players are found."""
        mock_response = Mock()
        mock_response.content = "<html><body><table></table></body></html>"
        mock_get_url.return_value = mock_response

        result = await pars_all_players_from_eesl.parse_all_players_from_eesl_index_page_eesl(
            base_url="http://test.com", start_page=0, limit=None, season_id=1
        )

        assert result == []

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_all_players_from_eesl.get_url")
    async def test_parse_all_players_from_eesl_index_page_eesl_with_limit(
        self, mock_get_url, mock_players_list_html
    ):
        """Test parsing with a limit on number of players."""
        mock_response = Mock()
        mock_response.content = mock_players_list_html
        mock_get_url.return_value = mock_response

        with (
            patch("src.pars_eesl.pars_all_players_from_eesl.file_service") as mock_fs,
            patch(
                "src.pars_eesl.pars_all_players_from_eesl.collect_players_dob_from_all_eesl"
            ) as mock_dob,
        ):
            mock_fs.download_and_resize_image = AsyncMock()
            mock_dob.return_value = datetime(1990, 1, 1)

            result = await pars_all_players_from_eesl.parse_all_players_from_eesl_index_page_eesl(
                base_url="http://test.com", start_page=0, limit=1, season_id=1
            )

            assert len(result) == 1
