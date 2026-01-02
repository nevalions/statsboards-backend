"""
Integration tests for MatchStatsWebSocketHandler.

These tests cover more complex WebSocket scenarios beyond the basic unit tests.
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from starlette.websockets import WebSocket, WebSocketState

from src.matches.stats_websocket_handler import MatchStatsWebSocketHandler
from tests.factories import (
    MatchFactory,
    TournamentFactory,
)


@pytest.mark.asyncio
@pytest.mark.integration
class TestMatchStatsWebSocketIntegration:
    """Integration tests for WebSocket handler scenarios."""

    async def test_multiple_clients_receive_broadcast(self, test_db, sport, season, teams_data):
        """Test that multiple connected clients receive broadcasts."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=920
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=120,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        from src.matches.stats_service import MatchStatsServiceDB

        stats_service = MatchStatsServiceDB(test_db)
        handler = MatchStatsWebSocketHandler(stats_service)

        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws3 = AsyncMock(spec=WebSocket)
        mock_ws1.application_state = WebSocketState.CONNECTED
        mock_ws2.application_state = WebSocketState.CONNECTED
        mock_ws3.application_state = WebSocketState.CONNECTED

        client_ids = ["client_1", "client_2", "client_3"]
        for i, ws in enumerate([mock_ws1, mock_ws2, mock_ws3]):
            handler.connected_clients[match.id] = handler.connected_clients.get(match.id, [])
            handler.connected_clients[match.id].append((ws, client_ids[i]))

        test_stats = {
            "match_id": match.id,
            "team_a": {"id": team_a.id, "team_stats": {}},
            "team_b": {"id": team_b.id, "team_stats": {}},
        }

        await handler.broadcast_stats(match.id, test_stats)

        assert mock_ws1.send_json.call_count == 1
        assert mock_ws2.send_json.call_count == 1
        assert mock_ws3.send_json.call_count == 1

    async def test_client_excluded_from_broadcast(self, test_db, sport, season, teams_data):
        """Test that a specific client can be excluded from broadcast."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=921
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=121,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        from src.matches.stats_service import MatchStatsServiceDB

        stats_service = MatchStatsServiceDB(test_db)
        handler = MatchStatsWebSocketHandler(stats_service)

        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws1.application_state = WebSocketState.CONNECTED
        mock_ws2.application_state = WebSocketState.CONNECTED

        handler.connected_clients[match.id] = [
            (mock_ws1, "client_1"),
            (mock_ws2, "client_2"),
        ]

        test_stats = {
            "match_id": match.id,
            "team_a": {"id": team_a.id, "team_stats": {}},
            "team_b": {"id": team_b.id, "team_stats": {}},
        }

        await handler.broadcast_stats(match.id, test_stats, exclude_client_id="client_1")

        assert mock_ws1.send_json.call_count == 0
        assert mock_ws2.send_json.call_count == 1

    async def test_disconnected_client_not_broadcasted(self, test_db, sport, season, teams_data):
        """Test that disconnected clients don't receive broadcasts."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=922
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=122,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        from src.matches.stats_service import MatchStatsServiceDB

        stats_service = MatchStatsServiceDB(test_db)
        handler = MatchStatsWebSocketHandler(stats_service)

        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws1.application_state = WebSocketState.CONNECTED
        mock_ws2.application_state = WebSocketState.DISCONNECTED

        handler.connected_clients[match.id] = [
            (mock_ws1, "client_1"),
            (mock_ws2, "client_2"),
        ]

        test_stats = {
            "match_id": match.id,
            "team_a": {"id": team_a.id, "team_stats": {}},
            "team_b": {"id": team_b.id, "team_stats": {}},
        }

        await handler.broadcast_stats(match.id, test_stats)

        assert mock_ws1.send_json.call_count == 1
        assert mock_ws2.send_json.call_count == 0

    async def test_no_clients_connected_no_broadcast(self, test_db, sport, season, teams_data):
        """Test that broadcast doesn't fail with no clients connected."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=923
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=123,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        from src.matches.stats_service import MatchStatsServiceDB

        stats_service = MatchStatsServiceDB(test_db)
        handler = MatchStatsWebSocketHandler(stats_service)

        test_stats = {
            "match_id": match.id,
            "team_a": {"id": team_a.id, "team_stats": {}},
            "team_b": {"id": team_b.id, "team_stats": {}},
        }

        await handler.broadcast_stats(match.id, test_stats)

        assert match.id not in handler.connected_clients
