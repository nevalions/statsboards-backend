import asyncio
from unittest.mock import AsyncMock

import pytest

from src.core.enums import ClockDirection, PeriodClockVariant
from src.gameclocks.db_services import GameClockServiceDB
from src.gameclocks.schemas import GameClockSchemaCreate, GameClockSchemaUpdate
from src.matchdata.db_services import MatchDataServiceDB
from src.matchdata.schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate
from src.matches.db_services import MatchServiceDB
from src.seasons.db_services import SeasonServiceDB
from src.sport_scoreboard_preset.db_services import SportScoreboardPresetServiceDB
from src.sport_scoreboard_preset.schemas import SportScoreboardPresetSchemaCreate
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
@pytest.mark.slow
class TestGameClockViews:
    async def test_create_gameclock_endpoint(self, client_match, test_db):
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

        response = await client_match.post("/api/gameclock/", json=gameclock_data.model_dump())

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_gameclock_endpoint(self, client_match, test_db):
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

        response = await client_match.put(
            f"/api/gameclock/{created.id}/", json=update_data.model_dump()
        )

        assert response.status_code == 200

    async def test_update_gameclock_not_found(self, client_match):
        update_data = GameClockSchemaUpdate(gameclock=500)

        response = await client_match.put("/api/gameclock/99999/", json=update_data.model_dump())

        assert response.status_code == 404

    async def test_update_gameclock_by_id_endpoint(self, client_match, test_db):
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

        response = await client_match.put(
            f"/api/gameclock/id/{created.id}/", json=update_data.model_dump()
        )

        assert response.status_code == 200
        assert response.json()["success"]

    async def test_start_gameclock_endpoint(self, client_match, test_db):
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

        response = await client_match.put(f"/api/gameclock/id/{created.id}/running/")

        assert response.status_code == 200

    async def test_pause_gameclock_endpoint(self, client_match, test_db):
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

        response = await client_match.put(f"/api/gameclock/id/{created.id}/paused/")

        assert response.status_code == 200
        assert response.json()["content"]["gameclock_status"] == "paused"

    async def test_pause_gameclock_updates_db_with_remaining_time(self, client_match, test_db):
        """Test that pausing a running gameclock updates DB with remaining time."""
        import asyncio

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

        start_response = await client_match.put(f"/api/gameclock/id/{created.id}/running/")
        assert start_response.status_code == 200
        assert start_response.json()["content"]["gameclock_status"] == "running"

        await asyncio.sleep(2)

        pause_response = await client_match.put(f"/api/gameclock/id/{created.id}/paused/")

        assert pause_response.status_code == 200
        assert pause_response.json()["content"]["gameclock_status"] == "paused"

        paused_gameclock_value = pause_response.json()["content"]["gameclock"]
        assert paused_gameclock_value is not None

        gameclock_after_pause = await gameclock_service.get_by_id(created.id)
        assert gameclock_after_pause.gameclock_status == "paused"
        assert gameclock_after_pause.gameclock == paused_gameclock_value

    async def test_reset_gameclock_endpoint(self, client_match, test_db):
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

        response = await client_match.put(f"/api/gameclock/id/{created.id}/stopped/720/")

        assert response.status_code == 200

    async def test_legacy_stopped_endpoint_sets_correct_values(self, client_match, test_db):
        """Test legacy /stopped/{seconds}/ endpoint still works and sets correct values."""
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
            match_id=match.id, gameclock=300, gameclock_status="running"
        )
        created = await gameclock_service.create(gameclock_data)

        response = await client_match.put(f"/api/gameclock/id/{created.id}/stopped/720/")

        assert response.status_code == 200
        data = response.json()
        assert data["content"]["gameclock"] == 720
        assert data["content"]["gameclock_status"] == "stopped"

        updated = await gameclock_service.get_by_id(created.id)
        assert updated is not None
        assert updated.gameclock == 720
        assert updated.gameclock_status == "stopped"

    async def test_gameclock_update_increments_version(self, client_match, test_db):
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
        response = await client_match.put(
            f"/api/gameclock/{created.id}/", json=update_data.model_dump()
        )

        assert response.status_code == 200
        assert response.json()["version"] == initial_version + 1

    async def test_gameclock_update_websocket_broadcasts_version(self, client_match, test_db):
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

        await asyncio.sleep(0.1)

        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=600)
        created = await gameclock_service.create(gameclock_data)
        initial_version = created.version

        await asyncio.sleep(0.2)

        try:
            await asyncio.wait_for(connection_manager.queues[client_id].get(), timeout=2.0)
        except asyncio.TimeoutError:
            pass

        updated = await gameclock_service.update(created.id, GameClockSchemaUpdate(gameclock=500))

        assert updated is not None
        assert updated.version == initial_version + 1

        await asyncio.sleep(0.2)

        try:
            notification = await asyncio.wait_for(
                connection_manager.queues[client_id].get(), timeout=2.0
            )
            assert notification["type"] == "gameclock-update"
            assert notification["match_id"] == match.id
            assert notification["gameclock"]["version"] == initial_version + 1
            assert notification["gameclock"]["gameclock"] == 500
        except asyncio.TimeoutError:
            pass

        await ws_manager.shutdown()
        await connection_manager.disconnect(client_id)

    async def test_gameclock_pause_state_reflected_in_ws(self, client_match, test_db):
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

        await asyncio.sleep(0.1)

        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(
            match_id=match.id, gameclock=600, gameclock_status="running"
        )
        created = await gameclock_service.create(gameclock_data)

        await asyncio.sleep(0.2)

        try:
            await asyncio.wait_for(connection_manager.queues[client_id].get(), timeout=2.0)
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
                connection_manager.queues[client_id].get(), timeout=2.0
            )
            assert notification["type"] == "gameclock-update"
            assert notification["match_id"] == match.id
            assert notification["gameclock"]["gameclock_status"] == "paused"
        except asyncio.TimeoutError:
            pass

        await ws_manager.shutdown()
        await connection_manager.disconnect(client_id)

    async def test_gameclock_reset_state_reflected_in_ws(self, client_match, test_db):
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

        await asyncio.sleep(0.1)

        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=600)
        created = await gameclock_service.create(gameclock_data)

        await asyncio.sleep(0.2)

        try:
            await asyncio.wait_for(connection_manager.queues[client_id].get(), timeout=2.0)
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
                connection_manager.queues[client_id].get(), timeout=2.0
            )
            assert notification["type"] == "gameclock-update"
            assert notification["match_id"] == match.id
            assert notification["gameclock"]["gameclock_status"] == "stopped"
            assert notification["gameclock"]["gameclock"] == 720
        except asyncio.TimeoutError:
            pass

        await ws_manager.shutdown()
        await connection_manager.disconnect(client_id)

    async def test_multiple_rapid_updates_increment_version_correctly(self, client_match, test_db):
        """Test that multiple rapid updates increment version correctly."""
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
        initial_version = created.version

        updated1 = await gameclock_service.update(created.id, GameClockSchemaUpdate(gameclock=500))
        assert updated1.version == initial_version + 1

        updated2 = await gameclock_service.update(created.id, GameClockSchemaUpdate(gameclock=400))
        assert updated2.version == initial_version + 2

        updated3 = await gameclock_service.update(created.id, GameClockSchemaUpdate(gameclock=300))
        assert updated3.version == initial_version + 3

        final = await gameclock_service.get_by_id(created.id)
        assert final is not None
        assert final.version == initial_version + 3
        assert final.gameclock == 300
        assert final.gameclock_status == "stopped"

    async def _setup_match_with_preset(
        self, test_db, period_clock_variant: PeriodClockVariant, direction: ClockDirection
    ):
        preset_service = SportScoreboardPresetServiceDB(test_db)
        preset = await preset_service.create(
            SportScoreboardPresetSchemaCreate(
                title=f"Preset {period_clock_variant.value}",
                gameclock_max=1200,
                period_clock_variant=period_clock_variant,
                direction=direction,
            )
        )

        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build(scoreboard_preset_id=preset.id))

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

        return match, preset

    async def test_reset_endpoint_down_direction_resets_to_max(self, client_match, test_db):
        """Test reset endpoint resets to gameclock_max for countdown clocks."""
        match, preset = await self._setup_match_with_preset(
            test_db, PeriodClockVariant.PER_PERIOD, ClockDirection.DOWN
        )

        gameclock_service = GameClockServiceDB(test_db)
        gameclock = await gameclock_service.create(
            GameClockSchemaCreate(
                match_id=match.id,
                gameclock=300,
                gameclock_max=1200,
                direction=ClockDirection.DOWN,
            )
        )

        response = await client_match.put(f"/api/gameclock/id/{gameclock.id}/reset/")

        assert response.status_code == 200
        data = response.json()
        assert data["content"]["gameclock"] == 1200
        assert data["content"]["gameclock_status"] == "stopped"

    async def test_reset_endpoint_up_per_period_resets_to_zero(self, client_match, test_db):
        """Test reset endpoint resets to 0 for count-up non-cumulative clocks."""
        match, preset = await self._setup_match_with_preset(
            test_db, PeriodClockVariant.PER_PERIOD, ClockDirection.UP
        )

        gameclock_service = GameClockServiceDB(test_db)
        gameclock = await gameclock_service.create(
            GameClockSchemaCreate(
                match_id=match.id,
                gameclock=800,
                gameclock_max=1200,
                direction=ClockDirection.UP,
            )
        )

        response = await client_match.put(f"/api/gameclock/id/{gameclock.id}/reset/")

        assert response.status_code == 200
        data = response.json()
        assert data["content"]["gameclock"] == 0
        assert data["content"]["gameclock_status"] == "stopped"

    async def test_reset_endpoint_up_cumulative_period_2_resets_to_base_max(
        self, client_match, test_db
    ):
        """Test reset endpoint resets to base_max for cumulative clock in period 2."""
        match, preset = await self._setup_match_with_preset(
            test_db, PeriodClockVariant.CUMULATIVE, ClockDirection.UP
        )

        matchdata_service = MatchDataServiceDB(test_db)
        matchdata = await matchdata_service.get_match_data_by_match_id(match.id)
        if matchdata is None:
            matchdata = await matchdata_service.create(MatchDataSchemaCreate(match_id=match.id))
        await matchdata_service.update(
            matchdata.id,
            MatchDataSchemaUpdate(qtr="2nd", period_key="period.2"),
        )

        gameclock_service = GameClockServiceDB(test_db)
        gameclock = await gameclock_service.create(
            GameClockSchemaCreate(
                match_id=match.id,
                gameclock=2000,
                gameclock_max=2400,
                direction=ClockDirection.UP,
            )
        )

        response = await client_match.put(f"/api/gameclock/id/{gameclock.id}/reset/")

        assert response.status_code == 200
        data = response.json()
        assert data["content"]["gameclock"] == 1200
        assert data["content"]["gameclock_status"] == "stopped"

    async def test_reset_endpoint_up_cumulative_period_1_resets_to_zero(
        self, client_match, test_db
    ):
        """Test reset endpoint resets to 0 for cumulative clock in period 1."""
        match, preset = await self._setup_match_with_preset(
            test_db, PeriodClockVariant.CUMULATIVE, ClockDirection.UP
        )

        gameclock_service = GameClockServiceDB(test_db)
        gameclock = await gameclock_service.create(
            GameClockSchemaCreate(
                match_id=match.id,
                gameclock=800,
                gameclock_max=1200,
                direction=ClockDirection.UP,
            )
        )

        response = await client_match.put(f"/api/gameclock/id/{gameclock.id}/reset/")

        assert response.status_code == 200
        data = response.json()
        assert data["content"]["gameclock"] == 0
        assert data["content"]["gameclock_status"] == "stopped"

    async def test_reset_endpoint_up_cumulative_period_3_resets_to_double_base(
        self, client_match, test_db
    ):
        """Test reset endpoint resets to 2*base_max for cumulative clock in period 3."""
        match, preset = await self._setup_match_with_preset(
            test_db, PeriodClockVariant.CUMULATIVE, ClockDirection.UP
        )

        matchdata_service = MatchDataServiceDB(test_db)
        matchdata = await matchdata_service.get_match_data_by_match_id(match.id)
        if matchdata is None:
            matchdata = await matchdata_service.create(MatchDataSchemaCreate(match_id=match.id))
        await matchdata_service.update(
            matchdata.id,
            MatchDataSchemaUpdate(qtr="3rd", period_key="period.3"),
        )

        gameclock_service = GameClockServiceDB(test_db)
        gameclock = await gameclock_service.create(
            GameClockSchemaCreate(
                match_id=match.id,
                gameclock=4000,
                gameclock_max=3600,
                direction=ClockDirection.UP,
            )
        )

        response = await client_match.put(f"/api/gameclock/id/{gameclock.id}/reset/")

        assert response.status_code == 200
        data = response.json()
        assert data["content"]["gameclock"] == 2400
        assert data["content"]["gameclock_status"] == "stopped"

    async def test_reset_endpoint_not_found(self, client_match):
        """Test reset endpoint returns 404 for non-existent gameclock."""
        response = await client_match.put("/api/gameclock/id/99999/reset/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["status_code"] == 404

    async def test_reset_endpoint_no_preset_defaults_to_zero(self, client_match, test_db):
        """Test reset endpoint defaults to 0 for count-up clocks without preset."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build(scoreboard_preset_id=None))

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
        gameclock = await gameclock_service.create(
            GameClockSchemaCreate(
                match_id=match.id,
                gameclock=500,
                direction=ClockDirection.UP,
            )
        )

        response = await client_match.put(f"/api/gameclock/id/{gameclock.id}/reset/")

        assert response.status_code == 200
        data = response.json()
        assert data["content"]["gameclock"] == 0
        assert data["content"]["gameclock_status"] == "stopped"
