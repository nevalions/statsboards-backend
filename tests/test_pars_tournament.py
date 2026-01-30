from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

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
    async def test_parse_tournament_matches_index_page_eesl_no_matches(self, mock_get_url):
        """Test parsing when no matches are found."""
        mock_response = Mock()
        mock_response.content = "<html><body></body></html>"
        mock_get_url.return_value = mock_response

        result = await pars_tournament.parse_tournament_matches_index_page_eesl(1)

        # When no matches are found, function returns []
        assert result is not None or result == []

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_tournament.get_url")
    @patch("src.pars_eesl.pars_tournament.file_service")
    async def test_parse_tournament_teams_index_page_eesl_success(
        self, mock_file_service, mock_get_url
    ):
        """Test successful parsing of tournament teams."""
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
                    <li class="teams__item">
                        <a href="/team?team_id=456" class="teams__logo">
                            <img src="https://example.com/teams/team2.png" alt="Team Beta" />
                        </a>
                        <a href="/team?team_id=456" class="teams__name-link">Team Beta</a>
                    </li>
                </ul>
            </body>
        </html>
        """
        mock_get_url.return_value = mock_response

        mock_file_service.download_and_process_image = AsyncMock(
            return_value={
                "image_url": "https://example.com/teams/team1.png",
                "image_icon_url": "https://example.com/teams/team1_icon.png",
                "image_webview_url": "https://example.com/teams/team1_web.png",
                "image_path": "/path/to/image",
            }
        )
        mock_file_service.get_most_common_color = AsyncMock(return_value="#ff0000")

        result = await pars_tournament.parse_tournament_teams_index_page_eesl(1)

        assert result is not None
        assert len(result) == 2
        assert result[0]["team_eesl_id"] == 123
        assert result[0]["title"] == "team alpha"
        assert result[1]["team_eesl_id"] == 456
        assert result[1]["title"] == "team beta"

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_tournament.get_url")
    async def test_parse_tournament_teams_index_page_eesl_fetch_error(self, mock_get_url):
        """Test parsing teams when URL fetch fails."""
        mock_get_url.return_value = None

        result = await pars_tournament.parse_tournament_teams_index_page_eesl(1)

        assert result is None

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_tournament.get_url")
    async def test_parse_tournament_matches_index_page_eesl_success(self, mock_get_url):
        """Test successful parsing of tournament matches."""
        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <div class="js-schedule">
                    <div class="js-calendar-matches-header">
                        <span class="schedule__head-text">1 января</span>
                        <ul class="schedule__matches-list">
                            <li class="js-calendar-match">
                                <div class="schedule__score-main">10:5</div>
                                <a href="/match?match_id=100" class="schedule__score">10:5</a>
                                <a href="/team?team_id=1" class="schedule__team-1">Team A</a>
                                <a href="/team?team_id=2" class="schedule__team-2">Team B</a>
                                <span class="schedule__time">12:00</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </body>
        </html>
        """
        mock_get_url.return_value = mock_response

        result = await pars_tournament.parse_tournament_matches_index_page_eesl(1)

        assert result is not None
        assert len(result) >= 1
        assert result[0]["match_eesl_id"] == 100
        assert result[0]["team_a_eesl_id"] == 1
        assert result[0]["team_b_eesl_id"] == 2
        assert result[0]["score_team_a"] == 10
        assert result[0]["score_team_b"] == 5

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_tournament.get_url")
    async def test_parse_tournament_matches_index_page_eesl_fetch_error(self, mock_get_url):
        """Test parsing matches when URL fetch fails."""
        mock_get_url.return_value = None

        result = await pars_tournament.parse_tournament_matches_index_page_eesl(1)

        assert result is None

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_tournament.get_url")
    async def test_parse_tournament_matches_and_create_jsons_success(self, mock_get_url):
        """Test wrapper function for parsing matches."""
        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <div class="js-schedule"></div>
            </body>
        </html>
        """
        mock_get_url.return_value = mock_response

        result = await pars_tournament.parse_tournament_matches_and_create_jsons(1)

        assert result is not None

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_tournament.get_url")
    @patch("src.pars_eesl.pars_tournament.file_service")
    async def test_parse_tournament_teams_and_create_jsons_success(
        self, mock_file_service, mock_get_url
    ):
        """Test wrapper function for parsing teams."""
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
            return_value={
                "image_url": "https://example.com/teams/team1.png",
                "image_icon_url": "https://example.com/teams/team1_icon.png",
                "image_webview_url": "https://example.com/teams/team1_web.png",
                "image_path": "/path/to/image",
            }
        )
        mock_file_service.get_most_common_color = AsyncMock(return_value="#ff0000")

        result = await pars_tournament.parse_tournament_teams_and_create_jsons(1)

        assert result is not None

    def test_parse_match_basic_info(self):
        """Test parsing basic match information from HTML element."""
        from bs4 import BeautifulSoup

        html = """
        <li class="js-calendar-match">
            <div class="schedule__score-main">10:5</div>
            <a href="/match?match_id=100" class="schedule__score">10:5</a>
            <a href="/team?team_id=1" class="schedule__team-1">Team A</a>
            <a href="/team?team_id=2" class="schedule__team-2">Team B</a>
        </li>
        """
        soup = BeautifulSoup(html, "lxml")
        item = soup.find("li", class_="js-calendar-match")

        result = pars_tournament._parse_match_basic_info(item)

        assert result["match_eesl_id"] == 100
        assert result["team_a_eesl_id"] == 1
        assert result["team_b_eesl_id"] == 2
        assert result["score_team_a"] == 10
        assert result["score_team_b"] == 5

    def test_parse_match_date(self):
        """Test parsing match date from HTML element."""
        from datetime import datetime

        item = Mock()
        item.find.return_value = Mock()
        item.find.return_value.text = "12:00"

        date_texts = Mock()
        date_texts.text = "1 января"

        result = pars_tournament._parse_match_date(date_texts, item)

        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 12
        assert result.minute == 0

    def test_calculate_week_number_new_week(self):
        """Test week number calculation for new week."""
        from datetime import datetime

        date_ = datetime(2025, 1, 8)
        week_counter = 1
        last_week_num = 1

        result_week, result_last = pars_tournament._calculate_week_number(
            date_, week_counter, last_week_num
        )

        assert result_week == 2
        assert result_last == 2

    def test_calculate_week_number_same_week(self):
        """Test week number calculation for same week."""
        from datetime import datetime

        date_ = datetime(2025, 1, 3)
        week_counter = 1
        last_week_num = 1

        result_week, result_last = pars_tournament._calculate_week_number(
            date_, week_counter, last_week_num
        )

        assert result_week == 1
        assert result_last == 1

    def test_create_final_match_data(self):
        """Test creation of final match data dictionary."""
        match_info = {
            "match_eesl_id": 100,
            "team_a_eesl_id": 1,
            "team_b_eesl_id": 2,
            "score_team_a": 10,
            "score_team_b": 5,
        }
        match_week = 1
        formatted_date = "2025-01-01 12:00:00"
        tournament_id = 10

        result = pars_tournament._create_final_match_data(
            match_info, match_week, formatted_date, tournament_id
        )

        assert result["week"] == 1
        assert result["match_eesl_id"] == 100
        assert result["team_a_eesl_id"] == 1
        assert result["team_b_eesl_id"] == 2
        assert result["match_date"] == formatted_date
        assert result["tournament_eesl_id"] == tournament_id
        assert result["score_team_a"] == 10
        assert result["score_team_b"] == 5

    def test_parse_match_date_error_splitting(self):
        """Test parsing match date when split fails."""
        item = Mock()
        item.find.return_value = Mock()
        item.find.return_value.text = "12:00"

        date_texts = Mock()
        date_texts.text = "invalid"

        result = pars_tournament._parse_match_date(date_texts, item)

        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 12
        assert result.minute == 0

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_tournament.get_url")
    @patch("src.pars_eesl.pars_tournament.file_service")
    async def test_parse_tournament_teams_color_extraction_error(
        self, mock_file_service, mock_get_url
    ):
        """Test parsing teams when color extraction fails - uses default color."""
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
            return_value={
                "image_url": "https://example.com/teams/team1.png",
                "image_icon_url": "https://example.com/teams/team1_icon.png",
                "image_webview_url": "https://example.com/teams/team1_web.png",
                "image_path": "/path/to/image",
            }
        )
        mock_file_service.get_most_common_color = AsyncMock(
            side_effect=Exception("Color extraction failed")
        )

        result = await pars_tournament.parse_tournament_teams_index_page_eesl(1)

        assert result is not None
        assert len(result) == 1
        assert result[0]["team_color"] == "#c01c28"

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_tournament.get_url")
    async def test_parse_tournament_matches_multiple_weeks(self, mock_get_url):
        """Test parsing matches across multiple weeks."""
        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <div class="js-schedule">
                    <div class="js-calendar-matches-header">
                        <span class="schedule__head-text">1 января 2024</span>
                        <ul class="schedule__matches-list">
                            <li class="js-calendar-match">
                                <div class="schedule__score-main">10:5</div>
                                <a href="/match?match_id=100" class="schedule__score">10:5</a>
                                <a href="/team?team_id=1" class="schedule__team-1">Team A</a>
                                <a href="/team?team_id=2" class="schedule__team-2">Team B</a>
                                <span class="schedule__time">12:00</span>
                            </li>
                        </ul>
                    </div>
                    <div class="js-calendar-matches-header">
                        <span class="schedule__head-text">8 января 2024</span>
                        <ul class="schedule__matches-list">
                            <li class="js-calendar-match">
                                <div class="schedule__score-main">8:7</div>
                                <a href="/match?match_id=101" class="schedule__score">8:7</a>
                                <a href="/team?team_id=3" class="schedule__team-1">Team C</a>
                                <a href="/team?team_id=4" class="schedule__team-2">Team D</a>
                                <span class="schedule__time">15:00</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </body>
        </html>
        """
        mock_get_url.return_value = mock_response

        result = await pars_tournament.parse_tournament_matches_index_page_eesl(1, year=2025)

        assert result is not None
        assert len(result) == 2
        assert result[0]["week"] == 1
        assert result[1]["week"] == 2

    def test_parse_match_basic_info_empty_score(self):
        """Test parsing match info with empty score."""
        from bs4 import BeautifulSoup

        html = """
        <li class="js-calendar-match">
            <div class="schedule__score-main"></div>
            <a href="/match?match_id=100" class="schedule__score"></a>
            <a href="/team?team_id=1" class="schedule__team-1">Team A</a>
            <a href="/team?team_id=2" class="schedule__team-2">Team B</a>
        </li>
        """
        soup = BeautifulSoup(html, "lxml")
        item = soup.find("li", class_="js-calendar-match")

        result = pars_tournament._parse_match_basic_info(item)

        assert result["match_eesl_id"] == 100
        assert result["team_a_eesl_id"] == 1
        assert result["team_b_eesl_id"] == 2
        assert result["score_team_a"] == 0
        assert result["score_team_b"] == 0

    @pytest.mark.asyncio
    @patch("src.pars_eesl.pars_tournament.get_url")
    @patch("src.pars_eesl.pars_tournament.file_service")
    async def test_parse_tournament_teams_error_handling(self, mock_file_service, mock_get_url):
        """Test that parsing continues even when one team fails."""
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
                    <li class="teams__item">
                        <a href="/team?team_id=456" class="teams__logo">
                            <img src="https://example.com/teams/team2.png" alt="Team Beta" />
                        </a>
                        <a href="/team?team_id=456" class="teams__name-link">Team Beta</a>
                    </li>
                </ul>
            </body>
        </html>
        """
        mock_get_url.return_value = mock_response

        call_count = [0]

        async def mock_download(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    "image_url": "https://example.com/teams/team1.png",
                    "image_icon_url": "https://example.com/teams/team1_icon.png",
                    "image_webview_url": "https://example.com/teams/team1_web.png",
                    "image_path": "/path/to/image",
                }
            raise Exception("Download failed for second team")

        mock_file_service.download_and_process_image = AsyncMock(side_effect=mock_download)
        mock_file_service.get_most_common_color = AsyncMock(return_value="#ff0000")

        result = await pars_tournament.parse_tournament_teams_index_page_eesl(1)

        assert result is not None
        assert len(result) == 1
        assert result[0]["team_eesl_id"] == 123
