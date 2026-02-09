"""Additional tests for stats_websocket_handler to improve coverage.

Run with:
    pytest tests/test_db_services/test_match_stats_websocket_handler_extended.py
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from src.matches.stats_websocket_handler import MatchStatsWebSocketHandler
from tests.factories import MatchFactory, TournamentFactory


@pytest.mark.asyncio
class TestMatchStatsWebSocketHandlerExtended:
    """Extended tests for MatchStatsWebSocketHandler to improve coverage."""

    async def test_send_initial_stats_exception(self, test_db, sport, season, teams_data):
        """Test exception handling when sending initial stats."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=900
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=100,
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

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.send_json = AsyncMock(side_effect=Exception("Send failed"))
        client_id = "test_client_1"

        await handler.send_initial_stats(mock_websocket, client_id, match.id)

        assert mock_websocket.send_json.called

    async def test_broadcast_stats_no_clients(self, test_db, sport, season, teams_data):
        """Test broadcasting when no clients are connected."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=900
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=100,
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

        test_stats = {"match_id": match.id, "team_a": {}, "team_b": {}}

        await handler.broadcast_stats(match.id, test_stats)

        assert match.id not in handler.connected_clients

    async def test_broadcast_stats_exclude_client(self, test_db, sport, season, teams_data):
        """Test broadcasting with client exclusion."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=900
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=100,
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

        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        mock_websocket1.application_state = WebSocketState.CONNECTED
        mock_websocket2.application_state = WebSocketState.CONNECTED
        client_id_1 = "test_client_1"
        client_id_2 = "test_client_2"

        handler.connected_clients[match.id] = [
            (mock_websocket1, client_id_1),
            (mock_websocket2, client_id_2),
        ]

        test_stats = {"match_id": match.id, "team_a": {}, "team_b": {}}

        await handler.broadcast_stats(match.id, test_stats, exclude_client_id=client_id_1)

        mock_websocket1.send_json.assert_not_called()
        mock_websocket2.send_json.assert_called_once()

    async def test_broadcast_stats_send_exception(self, test_db, sport, season, teams_data):
        """Test exception handling during broadcast."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=900
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=100,
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

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.send_json = AsyncMock(side_effect=Exception("Send failed"))
        client_id = "test_client_1"

        handler.connected_clients[match.id] = [(mock_websocket, client_id)]

        test_stats = {"match_id": match.id, "team_a": {}, "team_b": {}}

        await handler.broadcast_stats(match.id, test_stats)

        mock_websocket.send_json.assert_called_once()

    async def test_process_client_message_websocket_disconnect(
        self, test_db, sport, season, teams_data
    ):
        """Test processing client message with WebSocket disconnect."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=900
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=100,
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

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect(1000))
        client_id = "test_client_1"

        await handler.process_client_message(mock_websocket, client_id, match.id)

        mock_websocket.receive_json.assert_called_once()

    async def test_process_client_message_malformed_json(self, test_db, sport, season, teams_data):
        """Test processing client message with malformed JSON."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=900
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=100,
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

        import json

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.receive_json = AsyncMock(
            side_effect=[
                {"type": "stats_update", "timestamp": "2024-01-01T00:00:00", "stats": {}},
                json.JSONDecodeError("Malformed JSON", "{}", 0),
            ]
        )
        client_id = "test_client_1"

        await handler.process_client_message(mock_websocket, client_id, match.id)

        assert mock_websocket.receive_json.call_count >= 2

    async def test_handle_stats_update_missing_data(self, test_db, sport, season, teams_data):
        """Test handling stats update with missing data."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=900
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=100,
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

        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = "test_client_1"

        client_data_no_timestamp = {
            "type": "stats_update",
            "stats": {"test": "data"},
        }

        await handler.handle_stats_update(
            mock_websocket, client_id, match.id, client_data_no_timestamp
        )

        assert mock_websocket.send_json.call_count == 0

    async def test_handle_stats_update_invalid_timestamp(self, test_db, sport, season, teams_data):
        """Test handling stats update with invalid timestamp format."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=900
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=100,
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

        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = "test_client_1"

        client_data_invalid_timestamp = {
            "type": "stats_update",
            "timestamp": "invalid-timestamp",
            "stats": {"test": "data"},
        }

        await handler.handle_stats_update(
            mock_websocket, client_id, match.id, client_data_invalid_timestamp
        )

        assert mock_websocket.send_json.call_count == 0

    async def test_cleanup_connection_match_not_found(self, test_db, sport, season, teams_data):
        """Test cleanup when match is not in connected_clients."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=900
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=100,
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

        client_id = "test_client_1"

        await handler.cleanup_connection(client_id, match.id)

        assert match.id not in handler.connected_clients

    async def test_handle_websocket_connection_full_flow(self, test_db, sport, season, teams_data):
        """Test full WebSocket connection lifecycle."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=900
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=100,
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

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect(1000))
        client_id = "test_client_1"

        await handler.handle_websocket_connection(mock_websocket, client_id, match.id)

        mock_websocket.accept.assert_called_once()
        mock_websocket.receive_json.assert_called_once()
        mock_websocket.send_json.assert_called()
