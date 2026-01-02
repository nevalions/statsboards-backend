from datetime import datetime

import pytest
from starlette.websockets import WebSocket

from src.matches.stats_websocket_handler import MatchStatsWebSocketHandler
from tests.factories import (
    MatchFactory,
    TournamentFactory,
)


@pytest.mark.asyncio
class TestMatchStatsWebSocketHandler:
    """Test MatchStatsWebSocketHandler functionality."""

    async def test_send_initial_stats(self, test_db, sport, season, teams_data):
        """Test sending initial stats to new client."""
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

        mock_websocket = WebSocket()
        client_id = "test_client_1"

        await handler.send_initial_stats(mock_websocket, client_id, match.id)

        assert match.id in handler.last_write_timestamps

    async def test_broadcast_stats(self, test_db, sport, season, teams_data):
        """Test broadcasting stats to all connected clients."""
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

        mock_websocket1 = WebSocket()
        mock_websocket2 = WebSocket()
        client_id_1 = "test_client_1"
        client_id_2 = "test_client_2"

        handler.connected_clients[match.id] = [
            (mock_websocket1, client_id_1),
            (mock_websocket2, client_id_2),
        ]

        test_stats = {
            "match_id": match.id,
            "team_a": {"id": team_a.id, "team_stats": {}},
            "team_b": {"id": team_b.id, "team_stats": {}},
        }

        await handler.broadcast_stats(match.id, test_stats)

    async def test_handle_stats_update_client_wins(self, test_db, sport, season, teams_data):
        """Test handling stats update where client wins conflict."""
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

        mock_websocket = WebSocket()
        client_id = "test_client_1"

        future_timestamp = datetime.now()
        handler.last_write_timestamps[match.id] = datetime.min

        client_data = {
            "type": "stats_update",
            "timestamp": future_timestamp.isoformat(),
            "stats": {"test": "data"},
        }

        await handler.handle_stats_update(mock_websocket, client_id, match.id, client_data)

        assert handler.last_write_timestamps[match.id] == future_timestamp

    async def test_handle_stats_update_server_wins(self, test_db, sport, season, teams_data):
        """Test handling stats update where server wins conflict."""
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

        mock_websocket = WebSocket()
        client_id = "test_client_1"

        old_timestamp = datetime(2020, 1, 1)
        handler.last_write_timestamps[match.id] = datetime.now()

        client_data = {
            "type": "stats_update",
            "timestamp": old_timestamp.isoformat(),
            "stats": {"test": "data"},
        }

        await handler.handle_stats_update(mock_websocket, client_id, match.id, client_data)

        assert handler.last_write_timestamps[match.id] == datetime.now()

    async def test_cleanup_connection(self, test_db, sport, season, teams_data):
        """Test cleaning up disconnected client."""
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

        mock_websocket1 = WebSocket()
        mock_websocket2 = WebSocket()
        client_id_1 = "test_client_1"
        client_id_2 = "test_client_2"

        handler.connected_clients[match.id] = [
            (mock_websocket1, client_id_1),
            (mock_websocket2, client_id_2),
        ]

        await handler.cleanup_connection(client_id_1, match.id)

        assert len(handler.connected_clients[match.id]) == 1
        assert handler.connected_clients[match.id][0][1] == client_id_2
