from unittest.mock import Mock, patch

import pytest

from src.pars_eesl import parse_player_team_tournament
from src.pars_eesl.parse_player_team_tournament import ParsedPlayerTeamTournament


class TestParsePlayerTeamTournament:
    """Test suite for parsing player-team-tournament data from EESL."""

    @pytest.fixture
    def mock_player_team_tournament_html(self):
        """Mock HTML for player-team-tournament page with multiple players."""
        return """
        <html>
            <body>
                <table>
                    <tr class="table__row">
                        <td class="table__cell table__cell--number">10</td>
                        <td class="table__cell table__cell--amplua table__cell--amplua">
                            Forward
                        </td>
                        <td>
                            <a href="/player?id=123" class="table__player">
                                <span class="table__player-name">John Doe</span>
                            </a>
                        </td>
                    </tr>
                    <tr class="table__row">
                        <td class="table__cell table__cell--number">7</td>
                        <td class="table__cell table__cell--amplua table__cell--amplua">
                            Midfielder
                        </td>
                        <td>
                            <a href="/player?id=456" class="table__player">
                                <span class="table__player-name">Jane Smith</span>
                            </a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

    @pytest.fixture
    def mock_single_player_html(self):
        """Mock HTML with single player."""
        return """
        <html>
            <body>
                <table>
                    <tr class="table__row">
                        <td class="table__cell table__cell--number">10</td>
                        <td class="table__cell table__cell--amplua table__cell--amplua">
                            Forward
                        </td>
                        <td>
                            <a href="/player?id=123" class="table__player">
                                <span class="table__player-name">John Doe</span>
                            </a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

    @pytest.fixture
    def mock_no_players_html(self):
        """Mock HTML with no players."""
        return """
        <html>
            <body>
                <table></table>
            </body>
        </html>
        """

    @pytest.mark.asyncio
    @patch("src.pars_eesl.parse_player_team_tournament.get_url")
    async def test_parse_players_from_team_tournament_eesl_success_multiple_players(
        self, mock_get_url, mock_player_team_tournament_html
    ):
        """Test parsing multiple players from team-tournament page successfully."""
        mock_response = Mock()
        mock_response.content = mock_player_team_tournament_html
        mock_get_url.return_value = mock_response

        result = await parse_player_team_tournament.parse_players_from_team_tournament_eesl(
            eesl_tournament_id=19, eesl_team_id=1
        )

        assert result is not None
        assert len(result) == 2

        assert result[0]["eesl_tournament_id"] == 19
        assert result[0]["eesl_team_id"] == 1
        assert result[0]["player_eesl_id"] == 123
        assert result[0]["player_number"] == "10"
        assert result[0]["player_position"] == "forward"

        assert result[1]["eesl_tournament_id"] == 19
        assert result[1]["eesl_team_id"] == 1
        assert result[1]["player_eesl_id"] == 456
        assert result[1]["player_number"] == "7"
        assert result[1]["player_position"] == "midfielder"

    @pytest.mark.asyncio
    @patch("src.pars_eesl.parse_player_team_tournament.get_url")
    async def test_parse_players_from_team_tournament_eesl_success_single_player(
        self, mock_get_url, mock_single_player_html
    ):
        """Test parsing single player from team-tournament page successfully."""
        mock_response = Mock()
        mock_response.content = mock_single_player_html
        mock_get_url.return_value = mock_response

        result = await parse_player_team_tournament.parse_players_from_team_tournament_eesl(
            eesl_tournament_id=19, eesl_team_id=1
        )

        assert result is not None
        assert len(result) == 1
        assert result[0]["player_eesl_id"] == 123
        assert result[0]["player_number"] == "10"
        assert result[0]["player_position"] == "forward"

    @pytest.mark.asyncio
    @patch("src.pars_eesl.parse_player_team_tournament.get_url")
    async def test_parse_players_from_team_tournament_eesl_no_players(
        self, mock_get_url, mock_no_players_html
    ):
        """Test parsing when no players found - should return empty list."""
        mock_response = Mock()
        mock_response.content = mock_no_players_html
        mock_get_url.return_value = mock_response

        result = await parse_player_team_tournament.parse_players_from_team_tournament_eesl(
            eesl_tournament_id=19, eesl_team_id=1
        )

        assert result == []

    @pytest.mark.asyncio
    @patch("src.pars_eesl.parse_player_team_tournament.get_url")
    async def test_parse_players_from_team_tournament_eesl_url_construction(
        self, mock_get_url, mock_player_team_tournament_html
    ):
        """Test that URL is constructed correctly with tournament and team IDs."""
        mock_response = Mock()
        mock_response.content = mock_player_team_tournament_html
        mock_get_url.return_value = mock_response

        await parse_player_team_tournament.parse_players_from_team_tournament_eesl(
            eesl_tournament_id=42, eesl_team_id=99
        )

        mock_get_url.assert_called_once()
        args, _ = mock_get_url.call_args
        assert "42" in args[0]
        assert "99" in args[0]

    @pytest.mark.asyncio
    @patch("src.pars_eesl.parse_player_team_tournament.parse_players_from_team_tournament_eesl")
    async def test_parse_players_from_team_tournament_eesl_and_create_jsons_success(
        self, mock_parse
    ):
        """Test wrapper function returns parsed data successfully."""
        mock_parse.return_value = [
            ParsedPlayerTeamTournament(
                eesl_tournament_id=19,
                eesl_team_id=1,
                player_eesl_id=123,
                player_number="10",
                player_position="forward",
            )
        ]

        result = await parse_player_team_tournament.parse_players_from_team_tournament_eesl_and_create_jsons(
            eesl_tournament_id=19, eesl_team_id=1
        )

        assert result is not None
        assert len(result) == 1
        assert result[0]["player_eesl_id"] == 123

    @pytest.mark.asyncio
    @patch("src.pars_eesl.parse_player_team_tournament.parse_players_from_team_tournament_eesl")
    async def test_parse_players_from_team_tournament_eesl_and_create_jsons_error(self, mock_parse):
        """Test wrapper function raises exception on parsing error."""
        mock_parse.side_effect = Exception("Network error")

        with pytest.raises(Exception) as exc_info:
            await parse_player_team_tournament.parse_players_from_team_tournament_eesl_and_create_jsons(
                eesl_tournament_id=19, eesl_team_id=1
            )

        assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("src.pars_eesl.parse_player_team_tournament.get_url")
    async def test_parse_players_case_insensitive_values(self, mock_get_url):
        """Test that player number and position are converted to lowercase."""
        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <table>
                    <tr class="table__row">
                        <td class="table__cell table__cell--number">10</td>
                        <td class="table__cell table__cell--amplua table__cell--amplua">
                            FORWARD
                        </td>
                        <td>
                            <a href="/player?id=123" class="table__player">
                                <span class="table__player-name">John Doe</span>
                            </a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        mock_get_url.return_value = mock_response

        result = await parse_player_team_tournament.parse_players_from_team_tournament_eesl(
            eesl_tournament_id=19, eesl_team_id=1
        )

        assert result[0]["player_number"] == "10"
        assert result[0]["player_position"] == "forward"

    @pytest.mark.asyncio
    @patch("src.pars_eesl.parse_player_team_tournament.get_url")
    async def test_parse_players_malformed_html(self, mock_get_url):
        """Test parsing with malformed HTML - should handle gracefully."""
        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <table>
                    <tr class="table__row">
                        <td>
                            <a href="/player?id=123" class="table__player">
                                <span class="table__player-name">John Doe</span>
                            </a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        mock_get_url.return_value = mock_response

        result = await parse_player_team_tournament.parse_players_from_team_tournament_eesl(
            eesl_tournament_id=19, eesl_team_id=1
        )

        assert result is not None

    @pytest.mark.asyncio
    @patch("src.pars_eesl.parse_player_team_tournament.get_url")
    async def test_parse_players_custom_base_url(self, mock_get_url, mock_single_player_html):
        """Test parsing with custom base URL."""
        mock_response = Mock()
        mock_response.content = mock_single_player_html
        mock_get_url.return_value = mock_response

        await parse_player_team_tournament.parse_players_from_team_tournament_eesl(
            eesl_tournament_id=19, eesl_team_id=1, base_url="https://custom.com/"
        )

        args, _ = mock_get_url.call_args
        assert "custom.com" in args[0]

    def test_parsed_player_team_tournament_typeddict_structure(self):
        """Test that ParsedPlayerTeamTournament TypedDict has correct structure."""
        player: ParsedPlayerTeamTournament = {
            "eesl_tournament_id": 19,
            "eesl_team_id": 1,
            "player_eesl_id": 123,
            "player_number": "10",
            "player_position": "forward",
        }

        assert player["eesl_tournament_id"] == 19
        assert player["eesl_team_id"] == 1
        assert player["player_eesl_id"] == 123
        assert player["player_number"] == "10"
        assert player["player_position"] == "forward"
