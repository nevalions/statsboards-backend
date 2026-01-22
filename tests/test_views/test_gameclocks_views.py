import asyncio
from unittest.mock import AsyncMock

import pytest

from src.gameclocks.db_services import GameClockServiceDB
from src.gameclocks.schemas import GameClockSchemaCreate, GameClockSchemaUpdate
from src.matches.db_services import MatchServiceDB
from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import (
    MatchFactory,
    SeasonFactorySample,
    SportFactorySample,
    TeamFactory,
    TournamentFactory,
)


@pytest.mark.asyncio
class TestGameClockViews:
    async def test_create_gameclock_endpoint(self, client, test_db):
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
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=600)

        response = await client.post("/api/gameclock/", json=gameclock_data.model_dump())

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_gameclock_endpoint(self, client, test_db):
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
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=600)
        created = await gameclock_service.create(gameclock_data)

        update_data = GameClockSchemaUpdate(gameclock=500)

        response = await client.put(f"/api/gameclock/{created.id}/", json=update_data.model_dump())

        assert response.status_code == 200

    async def test_update_gameclock_not_found(self, client):
        update_data = GameClockSchemaUpdate(gameclock=500)

        response = await client.put("/api/gameclock/99999/", json=update_data.model_dump())

        assert response.status_code == 404

    async def test_update_gameclock_by_id_endpoint(self, client, test_db):
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
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=600)
        created = await gameclock_service.create(gameclock_data)

        update_data = GameClockSchemaUpdate(gameclock=500)

        response = await client.put(
            f"/api/gameclock/id/{created.id}/", json=update_data.model_dump()
        )

        assert response.status_code == 200
        assert response.json()["success"]

    async def test_start_gameclock_endpoint(self, client, test_db):
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
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(
            match_id=match.id, gameclock=600, gameclock_status="stopped"
        )
        created = await gameclock_service.create(gameclock_data)

        response = await client.put(f"/api/gameclock/id/{created.id}/running/")

        assert response.status_code == 200

    async def test_pause_gameclock_endpoint(self, client, test_db):
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
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(
            match_id=match.id, gameclock=600, gameclock_status="running"
        )
        created = await gameclock_service.create(gameclock_data)

        response = await client.put(f"/api/gameclock/id/{created.id}/paused/")

        assert response.status_code == 200

    async def test_reset_gameclock_endpoint(self, client, test_db):
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
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=300)
        created = await gameclock_service.create(gameclock_data)

        response = await client.put(f"/api/gameclock/id/{created.id}/stopped/720/")

        assert response.status_code == 200

    async def test_gameclock_update_increments_version(self, client, test_db):
        """Test that gameclock update increments version in REST response."""
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
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=600)
        created = await gameclock_service.create(gameclock_data)
        initial_version = created.version

        update_data = GameClockSchemaUpdate(gameclock=500)
        response = await client.put(f"/api/gameclock/{created.id}/", json=update_data.model_dump())

        assert response.status_code == 200
        assert response.json()["version"] == initial_version + 1

    async def test_gameclock_update_websocket_broadcasts_version(self, client, test_db):
        """Test that gameclock update broadcasts new version via WebSocket."""
        from src.core.config import settings
        from src.utils.websocket.websocket_manager import (
            MatchDataWebSocketManager,
            connection_manager,
        )

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
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        from starlette.websockets import WebSocket

        ws_manager = MatchDataWebSocketManager(db_url=str(settings.test_db.test_db_url_websocket()))
        await ws_manager.connect_to_db()

        client_id = "test_gameclock_version_client"
        await connection_manager.connect(AsyncMock(spec=WebSocket), client_id, match.id)
        ws_manager.gameclock_queues[client_id] = asyncio.Queue()

        await asyncio.sleep(0.1)

        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=600)
        created = await gameclock_service.create(gameclock_data)
        initial_version = created.version

        await asyncio.sleep(0.2)

        try:
            await asyncio.wait_for(ws_manager.gameclock_queues[client_id].get(), timeout=2.0)
        except asyncio.TimeoutError:
            pass

        updated = await gameclock_service.update(created.id, GameClockSchemaUpdate(gameclock=500))

        assert updated is not None
        assert updated.version == initial_version + 1

        await asyncio.sleep(0.2)

        try:
            notification = await asyncio.wait_for(
                ws_manager.gameclock_queues[client_id].get(), timeout=2.0
            )
            assert notification["type"] == "gameclock-update"
            assert notification["match_id"] == match.id
            assert notification["gameclock"]["version"] == initial_version + 1
            assert notification["gameclock"]["gameclock"] == 500
        except asyncio.TimeoutError:
            pass

        await ws_manager.shutdown()
        await connection_manager.disconnect(client_id)

    async def test_gameclock_pause_state_reflected_in_ws(self, client, test_db):
        """Test that paused gameclock state is reflected in WebSocket payload."""
        from src.core.config import settings
        from src.utils.websocket.websocket_manager import (
            MatchDataWebSocketManager,
            connection_manager,
        )

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
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        from starlette.websockets import WebSocket

        ws_manager = MatchDataWebSocketManager(db_url=str(settings.test_db.test_db_url_websocket()))
        await ws_manager.connect_to_db()

        client_id = "test_gameclock_pause_client"
        await connection_manager.connect(AsyncMock(spec=WebSocket), client_id, match.id)
        ws_manager.gameclock_queues[client_id] = asyncio.Queue()

        await asyncio.sleep(0.1)

        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(
            match_id=match.id, gameclock=600, gameclock_status="running"
        )
        created = await gameclock_service.create(gameclock_data)

        await asyncio.sleep(0.2)

        try:
            await asyncio.wait_for(ws_manager.gameclock_queues[client_id].get(), timeout=2.0)
        except asyncio.TimeoutError:
            pass

        updated = await gameclock_service.update(
            created.id, GameClockSchemaUpdate(gameclock_status="paused")
        )

        assert updated is not None
        assert updated.gameclock_status == "paused"

        await asyncio.sleep(0.2)

        try:
            notification = await asyncio.wait_for(
                ws_manager.gameclock_queues[client_id].get(), timeout=2.0
            )
            assert notification["type"] == "gameclock-update"
            assert notification["match_id"] == match.id
            assert notification["gameclock"]["gameclock_status"] == "paused"
        except asyncio.TimeoutError:
            pass

        await ws_manager.shutdown()
        await connection_manager.disconnect(client_id)

    async def test_gameclock_reset_state_reflected_in_ws(self, client, test_db):
        """Test that reset gameclock state is reflected in WebSocket payload."""
        from src.core.config import settings
        from src.utils.websocket.websocket_manager import (
            MatchDataWebSocketManager,
            connection_manager,
        )

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
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        from starlette.websockets import WebSocket

        ws_manager = MatchDataWebSocketManager(db_url=str(settings.test_db.test_db_url_websocket()))
        await ws_manager.connect_to_db()

        client_id = "test_gameclock_reset_client"
        await connection_manager.connect(AsyncMock(spec=WebSocket), client_id, match.id)
        ws_manager.gameclock_queues[client_id] = asyncio.Queue()

        await asyncio.sleep(0.1)

        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=600)
        created = await gameclock_service.create(gameclock_data)

        await asyncio.sleep(0.2)

        try:
            await asyncio.wait_for(ws_manager.gameclock_queues[client_id].get(), timeout=2.0)
        except asyncio.TimeoutError:
            pass

        updated = await gameclock_service.update(
            created.id, GameClockSchemaUpdate(gameclock=720, gameclock_status="stopped")
        )

        assert updated is not None
        assert updated.gameclock_status == "stopped"
        assert updated.gameclock == 720

        await asyncio.sleep(0.2)

        try:
            notification = await asyncio.wait_for(
                ws_manager.gameclock_queues[client_id].get(), timeout=2.0
            )
            assert notification["type"] == "gameclock-update"
            assert notification["match_id"] == match.id
            assert notification["gameclock"]["gameclock_status"] == "stopped"
            assert notification["gameclock"]["gameclock"] == 720
        except asyncio.TimeoutError:
            pass

        await ws_manager.shutdown()
        await connection_manager.disconnect(client_id)
