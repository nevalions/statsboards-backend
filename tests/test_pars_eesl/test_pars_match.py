"""Tests for pars_match module.

Run with:
    pytest tests/test_pars_eesl/test_pars_match.py
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from bs4 import BeautifulSoup


@pytest.mark.asyncio
class TestParseMatchIndexPageEesl:
    """Test parse_match_index_page_eesl function."""

    async def test_parse_match_success(self):
        """Test successful parsing of match data."""
        from src.pars_eesl.pars_match import parse_match_index_page_eesl

        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <div class="match-promo__score-main">10:5</div>
                <a class="match-protocol__team-name match-protocol__team-name--left" href="/team?id=1">Team A</a>
                <a class="match-protocol__team-name match-protocol__team-name--right" href="/team?id=2">Team B</a>
                <img class="match-promo__team-img" src="/logo_a.png" />
                <img class="match-promo__team-img" src="/logo_b.png" />
                <li class="match-protocol__member match-protocol__member--left">
                    <span class="match-protocol__member-number">10</span>
                    <span class="match-protocol__member-amplua">QB</span>
                    <a class="match-protocol__member-name" href="/player?id=100">John Doe</a>
                    <img class="match-protocol__member-img" src="/player100.jpg" />
                </li>
                <li class="match-protocol__member match-protocol__member--right">
                    <span class="match-protocol__member-number">20</span>
                    <span class="match-protocol__member-amplua">RB</span>
                    <a class="match-protocol__member-name" href="/player?id=200">Jane Smith</a>
                    <img class="match-protocol__member-img" src="/player200.jpg" />
                </li>
            </body>
        </html>
        """.encode()

        with patch("src.pars_eesl.pars_match.get_url", AsyncMock(return_value=mock_response)):
            result = await parse_match_index_page_eesl(123)

            assert result is not None
            assert result["team_a"] == "Team A"
            assert result["team_b"] == "Team B"
            assert result["team_a_eesl_id"] == 1
            assert result["team_b_eesl_id"] == 2
            assert result["score_a"] == "10"
            assert result["score_b"] == "5"
            assert result["team_logo_url_a"] == "/logo_a.png"
            assert result["team_logo_url_b"] == "/logo_b.png"
            assert len(result["roster_a"]) == 1
            assert len(result["roster_b"]) == 1
            assert result["roster_a"][0]["player_number"] == "10"
            assert result["roster_b"][0]["player_number"] == "20"

    async def test_parse_match_no_response(self):
        """Test parsing when URL fetch returns None."""
        from src.pars_eesl.pars_match import parse_match_index_page_eesl

        with patch("src.pars_eesl.pars_match.get_url", AsyncMock(return_value=None)):
            result = await parse_match_index_page_eesl(999)

            assert result is not None
            assert result["team_a"] == ""
            assert result["team_b"] == ""

    async def test_parse_match_no_team_links(self):
        """Test parsing when team links are missing."""
        from src.pars_eesl.pars_match import parse_match_index_page_eesl

        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <div class="match-promo__score-main">10:5</div>
            </body>
        </html>
        """.encode()

        with patch("src.pars_eesl.pars_match.get_url", AsyncMock(return_value=mock_response)):
            result = await parse_match_index_page_eesl(123)

            assert result is not None
            assert result["team_a"] == ""
            assert result["team_b"] == ""
            assert result["score_a"] == "10"
            assert result["score_b"] == "5"

    async def test_parse_match_no_score(self):
        """Test parsing when score element is missing."""
        from src.pars_eesl.pars_match import parse_match_index_page_eesl

        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <a class="match-protocol__team-name match-protocol__team-name--left" href="/team?id=1">Team A</a>
                <a class="match-protocol__team-name match-protocol__team-name--right" href="/team?id=2">Team B</a>
            </body>
        </html>
        """.encode()

        with patch("src.pars_eesl.pars_match.get_url", AsyncMock(return_value=mock_response)):
            result = await parse_match_index_page_eesl(123)

            assert result is not None
            assert result["score_a"] == ""
            assert result["score_b"] == ""

    async def test_parse_match_no_logos(self):
        """Test parsing when logo images are missing."""
        from src.pars_eesl.pars_match import parse_match_index_page_eesl

        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <a class="match-protocol__team-name match-protocol__team-name--left" href="/team?id=1">Team A</a>
                <a class="match-protocol__team-name match-protocol__team-name--right" href="/team?id=2">Team B</a>
            </body>
        </html>
        """.encode()

        with patch("src.pars_eesl.pars_match.get_url", AsyncMock(return_value=mock_response)):
            result = await parse_match_index_page_eesl(123)

            assert result is not None
            assert result["team_logo_url_a"] is None
            assert result["team_logo_url_b"] is None

    async def test_parse_match_empty_rosters(self):
        """Test parsing when rosters are empty."""
        from src.pars_eesl.pars_match import parse_match_index_page_eesl

        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <a class="match-protocol__team-name match-protocol__team-name--left" href="/team?id=1">Team A</a>
                <a class="match-protocol__team-name match-protocol__team-name--right" href="/team?id=2">Team B</a>
            </body>
        </html>
        """.encode()

        with patch("src.pars_eesl.pars_match.get_url", AsyncMock(return_value=mock_response)):
            result = await parse_match_index_page_eesl(123)

            assert result is not None
            assert result["roster_a"] == []
            assert result["roster_b"] == []

    async def test_parse_match_rosters_sorted(self):
        """Test that rosters are sorted by player number."""
        from src.pars_eesl.pars_match import parse_match_index_page_eesl

        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <a class="match-protocol__team-name match-protocol__team-name--left" href="/team?id=1">Team A</a>
                <a class="match-protocol__team-name match-protocol__team-name--right" href="/team?id=2">Team B</a>
                <li class="match-protocol__member match-protocol__member--left">
                    <span class="match-protocol__member-number">30</span>
                    <a class="match-protocol__member-name" href="/player?id=300">Player 3</a>
                </li>
                <li class="match-protocol__member match-protocol__member--left">
                    <span class="match-protocol__member-number">10</span>
                    <a class="match-protocol__member-name" href="/player?id=100">Player 1</a>
                </li>
                <li class="match-protocol__member match-protocol__member--left">
                    <span class="match-protocol__member-number">20</span>
                    <a class="match-protocol__member-name" href="/player?id=200">Player 2</a>
                </li>
            </body>
        </html>
        """.encode()

        with patch("src.pars_eesl.pars_match.get_url", AsyncMock(return_value=mock_response)):
            result = await parse_match_index_page_eesl(123)

            assert result is not None
            assert len(result["roster_a"]) == 3
            assert result["roster_a"][0]["player_number"] == "10"
            assert result["roster_a"][1]["player_number"] == "20"
            assert result["roster_a"][2]["player_number"] == "30"

    async def test_parse_match_exception_handling(self):
        """Test exception handling during parsing."""
        from src.pars_eesl.pars_match import parse_match_index_page_eesl

        with patch(
            "src.pars_eesl.pars_match.get_url", AsyncMock(side_effect=Exception("Network error"))
        ):
            result = await parse_match_index_page_eesl(123)

            assert result is None


@pytest.mark.asyncio
class TestGetPlayerEeslFromMatch:
    """Test get_player_eesl_from_match function."""

    async def test_get_player_success(self):
        """Test successful parsing of player data."""
        from src.pars_eesl.pars_match import get_player_eesl_from_match

        html = """
        <li class="match-protocol__member">
            <span class="match-protocol__member-number">10</span>
            <span class="match-protocol__member-amplua">QB</span>
            <a class="match-protocol__member-name" href="/player?id=100">John Doe</a>
            <img class="match-protocol__member-img" src="/player100.jpg" />
        </li>
        """
        soup = BeautifulSoup(html, "lxml")
        player_el = soup.find("li", class_="match-protocol__member")

        result = await get_player_eesl_from_match(player_el, "Team A", "/logo_a.png")

        assert result is not None
        assert result["player_number"] == "10"
        assert result["player_position"] == "QB"
        assert result["player_full_name"] == "John Doe"
        assert result["player_first_name"] == "John"
        assert result["player_second_name"] == "Doe"
        assert result["player_eesl_id"] == 100
        assert result["player_img_url"] == "/player100.jpg"
        assert result["player_team"] == "Team A"
        assert result["player_team_logo_url"] == "/logo_a.png"

    async def test_get_player_no_name(self):
        """Test parsing when player name element is missing."""
        from src.pars_eesl.pars_match import get_player_eesl_from_match

        html = """
        <li class="match-protocol__member">
            <span class="match-protocol__member-number">10</span>
            <span class="match-protocol__member-amplua">QB</span>
        </li>
        """
        soup = BeautifulSoup(html, "lxml")
        player_el = soup.find("li", class_="match-protocol__member")

        result = await get_player_eesl_from_match(player_el, "Team A", "/logo_a.png")

        assert result is not None
        assert result["player_full_name"] == ""
        assert result["player_first_name"] == ""
        assert result["player_second_name"] == ""
        assert result["player_eesl_id"] == 0

    async def test_get_player_no_link(self):
        """Test parsing when player link has no href."""
        from src.pars_eesl.pars_match import get_player_eesl_from_match

        html = """
        <li class="match-protocol__member">
            <span class="match-protocol__member-number">10</span>
            <a class="match-protocol__member-name">John Doe</a>
        </li>
        """
        soup = BeautifulSoup(html, "lxml")
        player_el = soup.find("li", class_="match-protocol__member")

        result = await get_player_eesl_from_match(player_el, "Team A", "/logo_a.png")

        assert result is not None
        assert result["player_eesl_id"] == 0

    async def test_get_player_single_name(self):
        """Test parsing when player has only one name."""
        from src.pars_eesl.pars_match import get_player_eesl_from_match

        html = """
        <li class="match-protocol__member">
            <span class="match-protocol__member-number">10</span>
            <a class="match-protocol__member-name" href="/player?id=100">John</a>
        </li>
        """
        soup = BeautifulSoup(html, "lxml")
        player_el = soup.find("li", class_="match-protocol__member")

        result = await get_player_eesl_from_match(player_el, "Team A", "/logo_a.png")

        assert result is not None
        assert result["player_first_name"] == "John"
        assert result["player_second_name"] == ""

    async def test_get_player_no_img(self):
        """Test parsing when player image is missing."""
        from src.pars_eesl.pars_match import get_player_eesl_from_match

        html = """
        <li class="match-protocol__member">
            <span class="match-protocol__member-number">10</span>
            <a class="match-protocol__member-name" href="/player?id=100">John Doe</a>
        </li>
        """
        soup = BeautifulSoup(html, "lxml")
        player_el = soup.find("li", class_="match-protocol__member")

        result = await get_player_eesl_from_match(player_el, "Team A", "/logo_a.png")

        assert result is not None
        assert result["player_img_url"] is None

    async def test_get_player_exception_handling(self):
        """Test exception handling during player parsing."""
        from src.pars_eesl.pars_match import get_player_eesl_from_match

        result = await get_player_eesl_from_match(None, "Team A", "/logo_a.png")

        assert result is None


@pytest.mark.asyncio
class TestParseMatchAndCreateJsons:
    """Test parse_match_and_create_jsons function."""

    async def test_parse_match_and_create_jsons_success(self):
        """Test successful match parsing and JSON creation."""
        from src.pars_eesl.pars_match import parse_match_and_create_jsons

        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <a class="match-protocol__team-name match-protocol__team-name--left" href="/team?id=1">Team A</a>
                <a class="match-protocol__team-name match-protocol__team-name--right" href="/team?id=2">Team B</a>
            </body>
        </html>
        """.encode()

        with patch("src.pars_eesl.pars_match.get_url", AsyncMock(return_value=mock_response)):
            result = await parse_match_and_create_jsons(123)

            assert result is not None
            assert result["team_a"] == "Team A"

    async def test_parse_match_and_create_jsons_exception(self):
        """Test exception handling in main parsing function."""
        from src.pars_eesl.pars_match import parse_match_and_create_jsons

        with patch(
            "src.pars_eesl.pars_match.get_url", AsyncMock(side_effect=Exception("Network error"))
        ):
            result = await parse_match_and_create_jsons(123)

            assert result is None
