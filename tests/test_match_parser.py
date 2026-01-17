from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.matches.parser import MatchParser


class TestMatchParser:
    @pytest.fixture
    def parser(self):
        return MatchParser()

    @pytest.mark.asyncio
    async def test_get_parse_tournament_matches(self, parser):
        with patch("src.matches.parser.parse_tournament_matches_index_page_eesl") as mock_parse:
            mock_parse.return_value = [
                {
                    "week": 1,
                    "match_eesl_id": 123,
                    "team_a_eesl_id": 1,
                    "team_b_eesl_id": 2,
                    "match_date": "2023-01-01",
                    "score_team_a": 3,
                    "score_team_b": 1,
                }
            ]

            result = await parser.get_parse_tournament_matches(123)

            assert result is not None
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_parse_tournament_matches_none(self, parser):
        with patch("src.matches.parser.parse_tournament_matches_index_page_eesl") as mock_parse:
            mock_parse.return_value = None

            result = await parser.get_parse_tournament_matches(123)

            assert result is None

    @pytest.mark.asyncio
    async def test_create_parsed_matches_no_tournament(self, parser):
        with patch("src.matches.parser.TournamentServiceDB") as mock_tournament_service:
            mock_instance = MagicMock()
            mock_instance.get_tournament_by_eesl_id = AsyncMock(return_value=None)
            mock_tournament_service.return_value = mock_instance

            mock_match_service = AsyncMock()

            result = await parser.create_parsed_matches(123, mock_match_service)

            assert result == []
            mock_match_service.create_or_update_match.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_parsed_matches_no_matches_list(self, parser):
        with (
            patch("src.matches.parser.TournamentServiceDB") as mock_tournament_service,
            patch("src.matches.parser.parse_tournament_matches_index_page_eesl") as mock_parse,
        ):
            mock_tournament_instance = MagicMock()
            mock_tournament_instance.get_tournament_by_eesl_id = AsyncMock(
                return_value=MagicMock(id=1)
            )
            mock_tournament_service.return_value = mock_tournament_instance

            mock_parse.return_value = None

            mock_match_service = AsyncMock()

            result = await parser.create_parsed_matches(123, mock_match_service)

            assert result == []

    @pytest.mark.asyncio
    async def test_create_parsed_matches_team_not_found(self, parser):
        with (
            patch("src.matches.parser.TournamentServiceDB") as mock_tournament_service,
            patch("src.matches.parser.parse_tournament_matches_index_page_eesl") as mock_parse,
            patch("src.matches.parser.db") as mock_db,
        ):
            mock_tournament_instance = MagicMock()
            mock_tournament_instance.get_tournament_by_eesl_id = AsyncMock(
                return_value=MagicMock(id=1)
            )
            mock_tournament_service.return_value = mock_tournament_instance

            mock_parse.return_value = [
                {
                    "week": 1,
                    "match_eesl_id": 123,
                    "team_a_eesl_id": 999,
                    "team_b_eesl_id": 2,
                    "match_date": "2023-01-01",
                    "score_team_a": 3,
                    "score_team_b": 1,
                }
            ]

            mock_db.async_session.return_value.__aenter__ = AsyncMock()
            mock_db.async_session.return_value.__aexit__ = AsyncMock()

            mock_session = MagicMock()
            mock_execute_result = MagicMock()
            mock_execute_result.scalars.return_value.all.return_value = []
            mock_session.execute.return_value = mock_execute_result
            mock_db.async_session.return_value.__aenter__.return_value = mock_session

            mock_match_service = AsyncMock()
            mock_match_service.create_or_update_match.return_value = MagicMock(id=1)

            result = await parser.create_parsed_matches(123, mock_match_service)

            assert result == []

    @pytest.mark.asyncio
    async def test_create_parsed_matches_exception(self, parser):
        with (
            patch("src.matches.parser.TournamentServiceDB") as mock_tournament_service,
            patch("src.matches.parser.parse_tournament_matches_index_page_eesl") as mock_parse,
        ):
            mock_tournament_instance = MagicMock()
            mock_tournament_instance.get_tournament_by_eesl_id = AsyncMock(
                return_value=MagicMock(id=1)
            )
            mock_tournament_service.return_value = mock_tournament_instance

            mock_parse.side_effect = Exception("DB Error")

            mock_match_service = AsyncMock()

            result = await parser.create_parsed_matches(123, mock_match_service)

            assert result == []
