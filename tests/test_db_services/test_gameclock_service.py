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
class TestGameClockServiceDB:
    async def test_create_gameclock(self, test_db):
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
            match_id=match.id,
            gameclock=720,
            gameclock_max=720,
            gameclock_status="stopped",
        )

        result = await gameclock_service.create(gameclock_data)

        assert result is not None
        assert result.id is not None
        assert result.match_id == match.id
        assert result.gameclock == 720

    async def test_create_gameclock_duplicate(self, test_db):
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
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=720)

        result1 = await gameclock_service.create(gameclock_data)
        result2 = await gameclock_service.create(gameclock_data)

        assert result1 is not None
        assert result2 is not None

    async def test_update_gameclock(self, test_db):
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
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=720)

        created = await gameclock_service.create(gameclock_data)
        update_data = GameClockSchemaUpdate(gameclock=600, gameclock_status="running")

        updated = await gameclock_service.update(created.id, update_data)

        assert updated.gameclock == 600
        assert updated.gameclock_status == "running"

    async def test_get_gameclock_by_match_id(self, test_db):
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
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=720)

        created = await gameclock_service.create(gameclock_data)
        result = await gameclock_service.get_gameclock_by_match_id(match.id)

        assert result is not None
        assert result.id == created.id

    async def test_get_gameclock_status(self, test_db):
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
            match_id=match.id, gameclock=720, gameclock_status="running"
        )

        created = await gameclock_service.create(gameclock_data)
        status = await gameclock_service.get_gameclock_status(created.id)

        assert status == "running"

    async def test_enable_match_data_gameclock_queues(self, test_db):
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
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=720)

        created = await gameclock_service.create(gameclock_data)
        queue = await gameclock_service.enable_match_data_gameclock_queues(created.id)

        assert queue is not None
        assert created.id in gameclock_service.clock_manager.active_gameclock_matches

    async def test_pause_gameclock_clears_started_at_ms(self, test_db):
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
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=720)

        created = await gameclock_service.create(gameclock_data)

        started_at_ms = 1234567890000
        await gameclock_service.update(
            created.id,
            GameClockSchemaUpdate(
                gameclock_status="running",
                gameclock_time_remaining=720,
                started_at_ms=started_at_ms,
            ),
        )

        running_clock = await gameclock_service.get_by_id(created.id)
        assert running_clock.started_at_ms == started_at_ms

        paused = await gameclock_service.update(
            created.id,
            GameClockSchemaUpdate(
                gameclock_status="paused",
                gameclock=720,
                gameclock_time_remaining=720,
                started_at_ms=None,
            ),
        )

        assert paused.started_at_ms is None
        assert paused.gameclock_status == "paused"

    async def test_delete_gameclock_cleans_up_resources(self, test_db):
        """Test that deleting a gameclock cleans up clock resources."""
        from src.clocks import clock_orchestrator

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
            match_id=match.id,
            gameclock=720,
            gameclock_max=720,
            gameclock_status="stopped",
        )

        created = await gameclock_service.create(gameclock_data)

        await gameclock_service.enable_match_data_gameclock_queues(created.id)

        assert created.id in gameclock_service.clock_manager.active_gameclock_matches
        assert created.id in gameclock_service.clock_manager.clock_state_machines

        await gameclock_service.delete(created.id)

        assert created.id not in gameclock_service.clock_manager.active_gameclock_matches
        assert created.id not in gameclock_service.clock_manager.clock_state_machines
        assert created.id not in clock_orchestrator.running_gameclocks

    async def test_stop_gameclock_internal_unregisters_from_orchestrator(self, test_db):
        """Test that _stop_gameclock_internal properly unregisters from orchestrator (STAB-191)."""
        from src.clocks import clock_orchestrator

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
            match_id=match.id, gameclock=720, gameclock_status="running"
        )

        created = await gameclock_service.create(gameclock_data)

        await gameclock_service.enable_match_data_gameclock_queues(created.id)

        assert created.id in gameclock_service.clock_manager.active_gameclock_matches
        assert created.id in gameclock_service.clock_manager.clock_state_machines
        assert created.id in clock_orchestrator.running_gameclocks

        await gameclock_service._stop_gameclock_internal(created.id)

        assert created.id not in clock_orchestrator.running_gameclocks
        assert created.id not in gameclock_service.clock_manager.clock_state_machines
