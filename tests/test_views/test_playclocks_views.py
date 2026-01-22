import asyncio
from unittest.mock import AsyncMock

import pytest

from src.matches.db_services import MatchServiceDB
from src.playclocks.db_services import PlayClockServiceDB
from src.playclocks.schemas import PlayClockSchemaCreate, PlayClockSchemaUpdate
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
class TestPlayClockViews:
    async def test_create_playclock_endpoint(self, client, test_db):
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

        playclock_data = PlayClockSchemaCreate(
            match_id=match.id, playclock=60, playclock_status="stopped"
        )

        response = await client.post("/api/playclock/", json=playclock_data.model_dump())

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_playclock_endpoint(self, client, test_db):
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

        playclock_service = PlayClockServiceDB(test_db)
        playclock_data = PlayClockSchemaCreate(
            match_id=match.id, playclock=60, playclock_status="stopped"
        )
        created = await playclock_service.create(playclock_data)

        update_data = PlayClockSchemaUpdate(playclock=120)

        response = await client.put(f"/api/playclock/{created.id}/", json=update_data.model_dump())

        assert response.status_code == 200

    async def test_update_playclock_not_found(self, client):
        update_data = PlayClockSchemaUpdate(playclock=120)

        response = await client.put("/api/playclock/99999/", json=update_data.model_dump())

        assert response.status_code == 404

    async def test_get_playclock_by_id_endpoint(self, client, test_db):
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

        playclock_service = PlayClockServiceDB(test_db)
        playclock_data = PlayClockSchemaCreate(
            match_id=match.id, playclock=60, playclock_status="stopped"
        )
        created = await playclock_service.create(playclock_data)

        response = await client.get(f"/api/playclock/id/{created.id}/")

        assert response.status_code == 200
        assert response.json()["content"]["id"] == created.id

    async def test_get_playclock_by_id_not_found(self, client):
        response = await client.get("/api/playclock/id/99999/")

        assert response.status_code == 404

    async def test_get_all_playclocks_endpoint(self, client, test_db):
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
        match2 = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        playclock_service = PlayClockServiceDB(test_db)
        await playclock_service.create(
            PlayClockSchemaCreate(match_id=match.id, playclock=60, playclock_status="stopped")
        )
        await playclock_service.create(
            PlayClockSchemaCreate(match_id=match2.id, playclock=90, playclock_status="stopped")
        )

        response = await client.get("/api/playclock/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_playclock_update_increments_version(self, client, test_db):
        """Test that playclock update increments version in REST response."""
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

        playclock_service = PlayClockServiceDB(test_db)
        playclock_data = PlayClockSchemaCreate(
            match_id=match.id, playclock=60, playclock_status="stopped"
        )
        created = await playclock_service.create(playclock_data)
        initial_version = created.version

        update_data = PlayClockSchemaUpdate(playclock=120)
        response = await client.put(f"/api/playclock/{created.id}/", json=update_data.model_dump())

        assert response.status_code == 200
        assert response.json()["version"] == initial_version + 1

    async def test_playclock_update_websocket_broadcasts_version(self, client, test_db):
        """Test that playclock update broadcasts new version via WebSocket."""
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

        client_id = "test_playclock_version_client"
        await connection_manager.connect(AsyncMock(spec=WebSocket), client_id, match.id)
        ws_manager.playclock_queues[client_id] = asyncio.Queue()

        await asyncio.sleep(0.1)

        playclock_service = PlayClockServiceDB(test_db)
        playclock_data = PlayClockSchemaCreate(
            match_id=match.id, playclock=60, playclock_status="stopped"
        )
        created = await playclock_service.create(playclock_data)
        initial_version = created.version

        await asyncio.sleep(0.2)

        try:
            await asyncio.wait_for(ws_manager.playclock_queues[client_id].get(), timeout=2.0)
        except asyncio.TimeoutError:
            pass

        updated = await playclock_service.update(created.id, PlayClockSchemaUpdate(playclock=120))

        assert updated is not None
        assert updated.version == initial_version + 1

        await asyncio.sleep(0.2)

        try:
            notification = await asyncio.wait_for(
                ws_manager.playclock_queues[client_id].get(), timeout=2.0
            )
            assert notification["type"] == "playclock-update"
            assert notification["match_id"] == match.id
            assert notification["playclock"]["version"] == initial_version + 1
            assert notification["playclock"]["playclock"] == 120
        except asyncio.TimeoutError:
            pass

        await ws_manager.shutdown()
        await connection_manager.disconnect(client_id)

    async def test_playclock_stopped_state_reflected_in_ws(self, client, test_db):
        """Test that stopped playclock state is reflected in WebSocket payload."""
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

        client_id = "test_playclock_stop_client"
        await connection_manager.connect(AsyncMock(spec=WebSocket), client_id, match.id)
        ws_manager.playclock_queues[client_id] = asyncio.Queue()

        await asyncio.sleep(0.1)

        playclock_service = PlayClockServiceDB(test_db)
        playclock_data = PlayClockSchemaCreate(
            match_id=match.id, playclock=60, playclock_status="running"
        )
        created = await playclock_service.create(playclock_data)

        await asyncio.sleep(0.2)

        try:
            await asyncio.wait_for(ws_manager.playclock_queues[client_id].get(), timeout=2.0)
        except asyncio.TimeoutError:
            pass

        updated = await playclock_service.update_with_none(
            created.id, PlayClockSchemaUpdate(playclock=None, playclock_status="stopped")
        )

        assert updated is not None
        assert updated.playclock_status == "stopped"
        assert updated.playclock is None

        await asyncio.sleep(0.2)

        try:
            notification = await asyncio.wait_for(
                ws_manager.playclock_queues[client_id].get(), timeout=2.0
            )
            assert notification["type"] == "playclock-update"
            assert notification["match_id"] == match.id
            assert notification["playclock"]["playclock_status"] == "stopped"
            assert notification["playclock"]["playclock"] is None
        except asyncio.TimeoutError:
            pass

        await ws_manager.shutdown()
        await connection_manager.disconnect(client_id)
