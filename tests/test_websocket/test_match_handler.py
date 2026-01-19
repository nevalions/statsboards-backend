import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState
from websockets import ConnectionClosedError, ConnectionClosedOK

from src.gameclocks.db_services import GameClockServiceDB
from src.gameclocks.schemas import GameClockSchemaCreate
from src.matchdata.db_services import MatchDataServiceDB
from src.matchdata.schemas import MatchDataSchemaCreate
from src.matches.db_services import MatchServiceDB
from src.matches.schemas import MatchSchemaCreate
from src.playclocks.db_services import PlayClockServiceDB
from src.playclocks.schemas import PlayClockSchemaCreate
from src.scoreboards.db_services import ScoreboardServiceDB
from src.scoreboards.schemas import ScoreboardSchemaCreate
from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB
from src.utils.websocket.websocket_manager import connection_manager
from src.websocket.match_handler import MatchWebSocketHandler
from tests.factories import (
    SeasonFactorySample,
    SportFactorySample,
    TeamFactory,
    TournamentFactory,
)


@pytest.mark.asyncio
@pytest.mark.integration
class TestMatchWebSocketHandlerSendInitialData:
    async def test_send_initial_data_success(self, test_db):
        """Test successful sending of initial data."""
        sport_service = SportServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        match_db_service = MatchDataServiceDB(test_db)
        await match_db_service.create(MatchDataSchemaCreate(match_id=created_match.id))

        playclock_service = PlayClockServiceDB(test_db)
        await playclock_service.create(PlayClockSchemaCreate(match_id=created_match.id))

        gameclock_service = GameClockServiceDB(test_db)
        await gameclock_service.create(GameClockSchemaCreate(match_id=created_match.id))

        scoreboard_db_service = ScoreboardServiceDB(test_db)
        await scoreboard_db_service.create(
            ScoreboardSchemaCreate(
                match_id=created_match.id,
                scale_tournament_logo=2,
                scale_main_sponsor=2,
                scale_logo_a=2,
                scale_logo_b=2,
                team_a_game_color="#ffffff",
                team_b_game_color="#000000",
                team_a_game_title="Team A",
                team_b_game_title="Team B",
            )
        )

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.send_json = AsyncMock()
        client_id = "test_client_initial"
        match_id = created_match.id

        await connection_manager.connect(mock_websocket, client_id, match_id)

        handler = MatchWebSocketHandler()
        await handler.send_initial_data(mock_websocket, client_id, match_id)

        assert mock_websocket.send_json.call_count == 3

        messages_sent = [call.args[0] for call in mock_websocket.send_json.call_args_list]

        message_types = [msg.get("type") for msg in messages_sent]
        assert "message-update" in message_types
        assert "playclock-update" in message_types
        assert "gameclock-update" in message_types

        queue = await connection_manager.get_queue_for_client(client_id)
        assert not queue.empty()

        for _ in range(3):
            await queue.get()

        await connection_manager.disconnect(client_id)

    async def test_send_initial_data_no_queue_warning(self, test_db):
        """Test warning when no queue exists for client."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        match_db_service = MatchDataServiceDB(test_db)
        await match_db_service.create(MatchDataSchemaCreate(match_id=created_match.id))

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.send_json = AsyncMock()
        client_id = "test_client_no_queue"
        match_id = created_match.id

        handler = MatchWebSocketHandler()
        await handler.send_initial_data(mock_websocket, client_id, match_id)

        assert mock_websocket.send_json.call_count == 3


@pytest.mark.asyncio
@pytest.mark.integration
class TestMatchWebSocketHandlerCleanup:
    async def test_cleanup_websocket_success(self, test_db):
        """Test successful WebSocket cleanup."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = "test_client_cleanup"
        match_id = created_match.id

        await connection_manager.connect(mock_websocket, client_id, match_id)

        handler = MatchWebSocketHandler()
        await handler.cleanup_websocket(client_id)

        active_connections = await connection_manager.get_active_connections()
        assert client_id not in active_connections

        match_subscriptions = await connection_manager.get_match_subscriptions(match_id)
        assert client_id not in match_subscriptions


@pytest.mark.asyncio
@pytest.mark.integration
class TestMatchWebSocketHandlerProcessData:
    async def test_process_data_websocket_success(self, test_db):
        """Test successful processing of WebSocket data."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.send_json = AsyncMock()
        client_id = "test_client_process"
        match_id = created_match.id

        await connection_manager.connect(mock_websocket, client_id, match_id)

        handler = MatchWebSocketHandler()

        task = asyncio.create_task(
            handler.process_data_websocket(mock_websocket, client_id, match_id)
        )

        queue = await connection_manager.get_queue_for_client(client_id)
        await queue.put({"type": "message-update", "match_id": match_id})

        await asyncio.sleep(0.1)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        await connection_manager.disconnect(client_id)

    async def test_process_data_websocket_disconnected(self, test_db):
        """Test processing when WebSocket is disconnected."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.DISCONNECTED
        client_id = "test_client_disconnected"
        match_id = created_match.id

        await connection_manager.connect(mock_websocket, client_id, match_id)

        handler = MatchWebSocketHandler()
        await handler.process_data_websocket(mock_websocket, client_id, match_id)

        await connection_manager.disconnect(client_id)

    async def test_process_data_websocket_unknown_message_type(self, test_db):
        """Test handling of unknown message types."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        client_id = "test_client_unknown_msg"
        match_id = created_match.id

        await connection_manager.connect(mock_websocket, client_id, match_id)

        handler = MatchWebSocketHandler()

        task = asyncio.create_task(
            handler.process_data_websocket(mock_websocket, client_id, match_id)
        )

        queue = await connection_manager.get_queue_for_client(client_id)
        await queue.put({"type": "unknown-type", "match_id": match_id})

        await asyncio.sleep(0.1)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        await connection_manager.disconnect(client_id)

    async def test_process_data_websocket_non_dict_message(self, test_db):
        """Test handling of non-dictionary messages."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        client_id = "test_client_non_dict"
        match_id = created_match.id

        await connection_manager.connect(mock_websocket, client_id, match_id)

        handler = MatchWebSocketHandler()

        task = asyncio.create_task(
            handler.process_data_websocket(mock_websocket, client_id, match_id)
        )

        queue = await connection_manager.get_queue_for_client(client_id)
        await queue.put("string_message")

        await asyncio.sleep(0.1)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        await connection_manager.disconnect(client_id)


@pytest.mark.asyncio
@pytest.mark.integration
class TestMatchWebSocketHandlerProcessMatchData:
    async def test_process_match_data_success(self, test_db):
        """Test successful processing of match data."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        match_db_service = MatchDataServiceDB(test_db)
        await match_db_service.create(MatchDataSchemaCreate(match_id=created_match.id))

        scoreboard_db_service = ScoreboardServiceDB(test_db)
        await scoreboard_db_service.create(
            ScoreboardSchemaCreate(
                match_id=created_match.id,
                scale_tournament_logo=2,
                scale_main_sponsor=2,
                scale_logo_a=2,
                scale_logo_b=2,
                team_a_game_color="#ffffff",
                team_b_game_color="#000000",
                team_a_game_title="Team A",
                team_b_game_title="Team B",
            )
        )

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.send_json = AsyncMock()
        match_id = created_match.id

        handler = MatchWebSocketHandler()
        await handler.process_match_data(mock_websocket, match_id)

        assert mock_websocket.send_json.call_count == 1
        message_sent = mock_websocket.send_json.call_args[0][0]
        assert message_sent.get("type") == "match-update"

    async def test_process_match_data_websocket_disconnected(self, test_db):
        """Test processing match data when WebSocket is disconnected."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.DISCONNECTED
        mock_websocket.send_json = AsyncMock()
        match_id = created_match.id

        handler = MatchWebSocketHandler()
        await handler.process_match_data(mock_websocket, match_id)

        assert mock_websocket.send_json.call_count == 0

    async def test_process_match_data_connection_closed_ok(self, test_db):
        """Test handling of ConnectionClosedOK during send."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        match_db_service = MatchDataServiceDB(test_db)
        await match_db_service.create(MatchDataSchemaCreate(match_id=created_match.id))

        scoreboard_db_service = ScoreboardServiceDB(test_db)
        await scoreboard_db_service.create(
            ScoreboardSchemaCreate(
                match_id=created_match.id,
                scale_tournament_logo=2,
                scale_main_sponsor=2,
                scale_logo_a=2,
                scale_logo_b=2,
                team_a_game_color="#ffffff",
                team_b_game_color="#000000",
                team_a_game_title="Team A",
                team_b_game_title="Team B",
            )
        )

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.send_json = AsyncMock(side_effect=ConnectionClosedOK(None, None))
        match_id = created_match.id

        handler = MatchWebSocketHandler()
        await handler.process_match_data(mock_websocket, match_id)

        assert mock_websocket.send_json.call_count == 1

    async def test_process_match_data_connection_closed_error(self, test_db):
        """Test handling of ConnectionClosedError during send."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        match_db_service = MatchDataServiceDB(test_db)
        await match_db_service.create(MatchDataSchemaCreate(match_id=created_match.id))

        scoreboard_db_service = ScoreboardServiceDB(test_db)
        await scoreboard_db_service.create(
            ScoreboardSchemaCreate(
                match_id=created_match.id,
                scale_tournament_logo=2,
                scale_main_sponsor=2,
                scale_logo_a=2,
                scale_logo_b=2,
                team_a_game_color="#ffffff",
                team_b_game_color="#000000",
                team_a_game_title="Team A",
                team_b_game_title="Team B",
            )
        )

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.send_json = AsyncMock(side_effect=ConnectionClosedError(None, None))
        match_id = created_match.id

        handler = MatchWebSocketHandler()
        await handler.process_match_data(mock_websocket, match_id)

        assert mock_websocket.send_json.call_count == 1

    async def test_process_match_data_exception_in_processing(self, test_db):
        """Test exception handling in process_match_data."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        with patch("src.helpers.fetch_helpers.fetch_with_scoreboard_data") as mock_fetch:
            mock_fetch.side_effect = Exception("Database error")

            mock_websocket = AsyncMock(spec=WebSocket)
            mock_websocket.application_state = WebSocketState.CONNECTED
            mock_websocket.send_json = AsyncMock()
            match_id = created_match.id

            handler = MatchWebSocketHandler()
            await handler.process_match_data(mock_websocket, match_id)

            assert mock_websocket.send_json.call_count == 0


@pytest.mark.asyncio
@pytest.mark.integration
class TestMatchWebSocketHandlerProcessGameclockData:
    async def test_process_gameclock_data_success(self, test_db):
        """Test successful processing of gameclock data."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        gameclock_service = GameClockServiceDB(test_db)
        await gameclock_service.create(GameClockSchemaCreate(match_id=created_match.id))

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.send_json = AsyncMock()
        match_id = created_match.id

        handler = MatchWebSocketHandler()
        await handler.process_gameclock_data(mock_websocket, match_id)

        assert mock_websocket.send_json.call_count == 1
        message_sent = mock_websocket.send_json.call_args[0][0]
        assert message_sent.get("type") == "gameclock-update"

    async def test_process_gameclock_data_websocket_disconnected(self, test_db):
        """Test processing gameclock data when WebSocket is disconnected."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.DISCONNECTED
        mock_websocket.send_json = AsyncMock()
        match_id = created_match.id

        handler = MatchWebSocketHandler()
        await handler.process_gameclock_data(mock_websocket, match_id)

        assert mock_websocket.send_json.call_count == 0

    async def test_process_gameclock_data_connection_closed_ok(self, test_db):
        """Test handling of ConnectionClosedOK during gameclock send."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        gameclock_service = GameClockServiceDB(test_db)
        await gameclock_service.create(GameClockSchemaCreate(match_id=created_match.id))

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.send_json = AsyncMock(side_effect=ConnectionClosedOK(None, None))
        match_id = created_match.id

        handler = MatchWebSocketHandler()
        await handler.process_gameclock_data(mock_websocket, match_id)

        assert mock_websocket.send_json.call_count == 1


@pytest.mark.asyncio
@pytest.mark.integration
class TestMatchWebSocketHandlerProcessPlayclockData:
    async def test_process_playclock_data_success(self, test_db):
        """Test successful processing of playclock data."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        playclock_service = PlayClockServiceDB(test_db)
        await playclock_service.create(PlayClockSchemaCreate(match_id=created_match.id))

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.send_json = AsyncMock()
        match_id = created_match.id

        handler = MatchWebSocketHandler()
        await handler.process_playclock_data(mock_websocket, match_id)

        assert mock_websocket.send_json.call_count == 1
        message_sent = mock_websocket.send_json.call_args[0][0]
        assert message_sent.get("type") == "playclock-update"

    async def test_process_playclock_data_websocket_disconnected(self, test_db):
        """Test processing playclock data when WebSocket is disconnected."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.DISCONNECTED
        mock_websocket.send_json = AsyncMock()
        match_id = created_match.id

        handler = MatchWebSocketHandler()
        await handler.process_playclock_data(mock_websocket, match_id)

        assert mock_websocket.send_json.call_count == 0

    async def test_process_playclock_data_connection_closed_ok(self, test_db):
        """Test handling of ConnectionClosedOK during playclock send."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        playclock_service = PlayClockServiceDB(test_db)
        await playclock_service.create(PlayClockSchemaCreate(match_id=created_match.id))

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.send_json = AsyncMock(side_effect=ConnectionClosedOK(None, None))
        match_id = created_match.id

        handler = MatchWebSocketHandler()
        await handler.process_playclock_data(mock_websocket, match_id)

        assert mock_websocket.send_json.call_count == 1


@pytest.mark.asyncio
@pytest.mark.integration
class TestMatchWebSocketHandlerHandleConnection:
    async def test_handle_websocket_connection_success(self, test_db):
        """Test successful WebSocket connection handling."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        match_db_service = MatchDataServiceDB(test_db)
        await match_db_service.create(MatchDataSchemaCreate(match_id=created_match.id))

        playclock_service = PlayClockServiceDB(test_db)
        await playclock_service.create(PlayClockSchemaCreate(match_id=created_match.id))

        gameclock_service = GameClockServiceDB(test_db)
        await gameclock_service.create(GameClockSchemaCreate(match_id=created_match.id))

        scoreboard_db_service = ScoreboardServiceDB(test_db)
        await scoreboard_db_service.create(
            ScoreboardSchemaCreate(
                match_id=created_match.id,
                scale_tournament_logo=2,
                scale_main_sponsor=2,
                scale_logo_a=2,
                scale_logo_b=2,
                team_a_game_color="#ffffff",
                team_b_game_color="#000000",
                team_a_game_title="Team A",
                team_b_game_title="Team B",
            )
        )

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.send_json = AsyncMock()
        client_id = "test_client_handle"
        match_id = created_match.id

        handler = MatchWebSocketHandler()

        task = asyncio.create_task(
            handler.handle_websocket_connection(mock_websocket, client_id, match_id)
        )

        await asyncio.sleep(0.1)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert mock_websocket.accept.called

        active_connections = await connection_manager.get_active_connections()
        assert client_id not in active_connections

    async def test_handle_websocket_connection_disconnect_error(self, test_db):
        """Test handling WebSocketDisconnect error."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock(side_effect=WebSocketDisconnect(1000))
        mock_websocket.application_state = WebSocketState.CONNECTED
        client_id = "test_client_disconnect"
        match_id = created_match.id

        handler = MatchWebSocketHandler()
        await handler.handle_websocket_connection(mock_websocket, client_id, match_id)

        active_connections = await connection_manager.get_active_connections()
        assert client_id not in active_connections

    async def test_handle_websocket_connection_timeout_error(self, test_db):
        """Test handling TimeoutError."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_websocket.application_state = WebSocketState.CONNECTED
        client_id = "test_client_timeout"
        match_id = created_match.id

        handler = MatchWebSocketHandler()
        await handler.handle_websocket_connection(mock_websocket, client_id, match_id)

    async def test_handle_websocket_connection_runtime_error(self, test_db):
        """Test handling RuntimeError."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock(side_effect=RuntimeError("Test error"))
        mock_websocket.application_state = WebSocketState.CONNECTED
        client_id = "test_client_runtime"
        match_id = created_match.id

        handler = MatchWebSocketHandler()
        await handler.handle_websocket_connection(mock_websocket, client_id, match_id)
