import pytest
from pydantic import ValidationError

from src.core.enums import (
    ClockDirection,
    ClockOnStopBehavior,
    ClockStatus,
    InitialTimeMode,
    PeriodClockVariant,
    SportPeriodMode,
)
from src.gameclocks.schemas import GameClockSchemaCreate
from src.matchdata.db_services import MatchDataServiceDB
from src.matchdata.schemas import MatchDataSchemaCreate
from src.matches.db_services import MatchServiceDB
from src.playclocks.db_services import PlayClockServiceDB
from src.playclocks.schemas import PlayClockSchemaCreate
from src.scoreboards.db_services import ScoreboardServiceDB
from src.scoreboards.schemas import ScoreboardSchemaCreate
from src.seasons.db_services import SeasonServiceDB
from src.sport_scoreboard_preset.db_services import SportScoreboardPresetServiceDB
from src.sport_scoreboard_preset.schemas import (
    SportScoreboardPresetSchemaCreate,
    SportScoreboardPresetSchemaUpdate,
)
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import (
    MatchFactory,
    SeasonFactorySample,
    SportFactoryAny,
    TeamFactory,
    TournamentFactory,
)


@pytest.mark.asyncio
class TestSportScoreboardPresetServiceDB:
    async def test_create_preset(self, test_db):
        service = SportScoreboardPresetServiceDB(test_db)
        preset_data = SportScoreboardPresetSchemaCreate(
            title="Basketball Preset",
            gameclock_max=720,
            direction=ClockDirection.DOWN,
            on_stop_behavior=ClockOnStopBehavior.HOLD,
            is_qtr=True,
            is_time=True,
            is_playclock=True,
            is_downdistance=False,
            has_timeouts=True,
            has_playclock=True,
            period_mode=SportPeriodMode.QTR,
            period_count=4,
            period_labels_json=None,
            default_playclock_seconds=30,
        )

        result = await service.create(preset_data)

        assert result is not None
        assert result.id is not None
        assert result.title == "Basketball Preset"
        assert result.gameclock_max == 720
        assert result.initial_time_mode == InitialTimeMode.MAX
        assert result.initial_time_min_seconds is None
        assert result.period_clock_variant == PeriodClockVariant.PER_PERIOD
        assert result.direction == ClockDirection.DOWN
        assert result.on_stop_behavior == ClockOnStopBehavior.HOLD
        assert result.is_qtr is True
        assert result.is_time is True
        assert result.is_playclock is True
        assert result.is_downdistance is False
        assert result.has_timeouts is True
        assert result.has_playclock is True
        assert result.period_mode == "qtr"
        assert result.period_count == 4
        assert result.period_labels_json is None
        assert result.default_playclock_seconds == 30

    async def test_create_preset_with_min_initial_time_mode(self, test_db):
        service = SportScoreboardPresetServiceDB(test_db)

        preset_data = SportScoreboardPresetSchemaCreate(
            title="Min Initial Time Preset",
            initial_time_mode=InitialTimeMode.MIN,
            initial_time_min_seconds=120,
        )

        result = await service.create(preset_data)

        assert result.initial_time_mode == InitialTimeMode.MIN
        assert result.initial_time_min_seconds == 120

    async def test_get_preset_by_id(self, test_db):
        service = SportScoreboardPresetServiceDB(test_db)
        preset_data = SportScoreboardPresetSchemaCreate(title="Football Preset")

        created = await service.create(preset_data)
        result = await service.get_by_id(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.title == "Football Preset"
        assert result.has_timeouts is True
        assert result.has_playclock is True
        assert result.period_mode == "qtr"
        assert result.period_count == 4
        assert result.period_labels_json is None
        assert result.default_playclock_seconds is None
        assert result.initial_time_mode == InitialTimeMode.MAX
        assert result.initial_time_min_seconds is None
        assert result.period_clock_variant == PeriodClockVariant.PER_PERIOD

    async def test_update_preset(self, test_db):
        service = SportScoreboardPresetServiceDB(test_db)
        preset_data = SportScoreboardPresetSchemaCreate(title="Soccer Preset")

        created = await service.create(preset_data)
        update_data = SportScoreboardPresetSchemaUpdate(
            title="Soccer Preset Updated",
            gameclock_max=900,
            period_clock_variant=PeriodClockVariant.CUMULATIVE,
            direction=ClockDirection.UP,
            has_timeouts=False,
            has_playclock=False,
            period_mode=SportPeriodMode.CUSTOM,
            period_count=2,
            period_labels_json=["period.leg_1", "period.leg_2"],
            default_playclock_seconds=25,
        )

        updated = await service.update(created.id, update_data)

        assert updated.title == "Soccer Preset Updated"
        assert updated.gameclock_max == 900
        assert updated.period_clock_variant == PeriodClockVariant.CUMULATIVE
        assert updated.direction == ClockDirection.UP
        assert updated.initial_time_mode == InitialTimeMode.MAX
        assert updated.has_timeouts is False
        assert updated.has_playclock is False
        assert updated.period_mode == "custom"
        assert updated.period_count == 2
        assert updated.period_labels_json == ["period.leg_1", "period.leg_2"]
        assert updated.default_playclock_seconds == 25

    async def test_create_preset_rejects_non_machine_period_labels(self, test_db):
        _ = SportScoreboardPresetServiceDB(test_db)

        with pytest.raises(ValidationError):
            SportScoreboardPresetSchemaCreate(
                title="Invalid Labels",
                period_mode=SportPeriodMode.CUSTOM,
                period_count=2,
                period_labels_json=["Leg 1", "тайм 2"],
            )

    async def test_create_preset_rejects_custom_count_labels_mismatch(self, test_db):
        _ = SportScoreboardPresetServiceDB(test_db)

        with pytest.raises(ValidationError):
            SportScoreboardPresetSchemaCreate(
                title="Invalid Custom Count",
                period_mode=SportPeriodMode.CUSTOM,
                period_count=3,
                period_labels_json=["period.leg_1", "period.leg_2"],
            )

    async def test_create_preset_rejects_min_initial_time_mode_without_seconds(self, test_db):
        _ = SportScoreboardPresetServiceDB(test_db)

        with pytest.raises(ValidationError):
            SportScoreboardPresetSchemaCreate(
                title="Invalid Min Mode",
                initial_time_mode=InitialTimeMode.MIN,
            )

    async def test_create_preset_allows_zero_initial_time_mode_without_seconds(self, test_db):
        _ = SportScoreboardPresetServiceDB(test_db)

        schema = SportScoreboardPresetSchemaCreate(
            title="Zero Mode",
            initial_time_mode=InitialTimeMode.ZERO,
            initial_time_min_seconds=None,
        )

        assert schema.initial_time_mode == InitialTimeMode.ZERO
        assert schema.initial_time_min_seconds is None

    async def test_update_preset_rejects_min_initial_time_mode_without_seconds(self, test_db):
        _ = SportScoreboardPresetServiceDB(test_db)

        with pytest.raises(ValidationError):
            SportScoreboardPresetSchemaUpdate(
                initial_time_mode=InitialTimeMode.MIN,
            )

    async def test_create_preset_rejects_period_labels_outside_custom_mode(self, test_db):
        _ = SportScoreboardPresetServiceDB(test_db)

        with pytest.raises(ValidationError):
            SportScoreboardPresetSchemaCreate(
                title="Invalid Mode Labels",
                period_mode=SportPeriodMode.QTR,
                period_labels_json=["period.q1", "period.q2"],
            )

    async def test_delete_preset(self, test_db):
        service = SportScoreboardPresetServiceDB(test_db)
        preset_data = SportScoreboardPresetSchemaCreate(title="Hockey Preset")

        created = await service.create(preset_data)
        await service.delete(created.id)

        result = await service.get_by_id(created.id)
        assert result is None

    async def test_get_all_presets(self, test_db):
        service = SportScoreboardPresetServiceDB(test_db)

        await service.create(SportScoreboardPresetSchemaCreate(title="Preset 1"))
        await service.create(SportScoreboardPresetSchemaCreate(title="Preset 2"))
        await service.create(SportScoreboardPresetSchemaCreate(title="Preset 3"))

        results = await service.get_all_elements()

        assert len(results) == 3

    async def test_link_preset_to_sport(self, test_db):
        preset_service = SportScoreboardPresetServiceDB(test_db)
        sport_service = SportServiceDB(test_db)

        preset = await preset_service.create(
            SportScoreboardPresetSchemaCreate(title="Volleyball Preset")
        )
        sport = await sport_service.create(SportFactoryAny.build(scoreboard_preset_id=preset.id))

        assert sport.scoreboard_preset_id == preset.id

    async def test_get_sports_by_preset(self, test_db):
        preset_service = SportScoreboardPresetServiceDB(test_db)
        sport_service = SportServiceDB(test_db)

        preset = await preset_service.create(
            SportScoreboardPresetSchemaCreate(title="Tennis Preset")
        )

        sport1 = await sport_service.create(
            SportFactoryAny.build(scoreboard_preset_id=preset.id, title="Tennis 1")
        )
        sport2 = await sport_service.create(
            SportFactoryAny.build(scoreboard_preset_id=preset.id, title="Tennis 2")
        )
        _ = await sport_service.create(
            SportFactoryAny.build(scoreboard_preset_id=None, title="Other Sport")
        )

        sports = await preset_service.get_sports_by_preset(preset.id)

        assert len(sports) == 2
        sport_ids = [s.id for s in sports]
        assert sport1.id in sport_ids
        assert sport2.id in sport_ids

    async def test_preset_update_propagates_to_scoreboard(self, test_db):
        preset_service = SportScoreboardPresetServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        match_service = MatchServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        scoreboard_service = ScoreboardServiceDB(test_db)

        preset = await preset_service.create(
            SportScoreboardPresetSchemaCreate(
                title="Rugby Preset",
                is_qtr=True,
                period_mode=SportPeriodMode.QTR,
                period_count=4,
                is_time=True,
                is_playclock=True,
                is_downdistance=True,
            )
        )

        sport = await sport_service.create(SportFactoryAny.build(scoreboard_preset_id=preset.id))

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        scoreboard = await scoreboard_service.create(
            ScoreboardSchemaCreate(
                match_id=match.id,
                use_sport_preset=True,
                is_qtr=False,
                period_mode=SportPeriodMode.PERIOD,
                period_count=3,
                period_labels_json=["period.1", "period.2", "period.3"],
                is_time=False,
                is_playclock=False,
                is_downdistance=False,
            )
        )

        assert scoreboard.use_sport_preset is True
        assert scoreboard.is_qtr is False

        await preset_service.update(
            preset.id,
            SportScoreboardPresetSchemaUpdate(
                is_qtr=False,
                period_mode=SportPeriodMode.HALF,
                period_count=2,
                period_labels_json=None,
                is_time=False,
                is_playclock=False,
                is_downdistance=False,
            ),
        )

        updated_scoreboard = await scoreboard_service.get_by_id(scoreboard.id)
        assert updated_scoreboard.is_qtr is False
        assert updated_scoreboard.period_mode == "half"
        assert updated_scoreboard.period_count == 2
        assert updated_scoreboard.period_labels_json is None
        assert updated_scoreboard.is_time is False
        assert updated_scoreboard.is_playclock is False
        assert updated_scoreboard.is_downdistance is False

    async def test_preset_update_respects_use_sport_preset_flag(self, test_db):
        preset_service = SportScoreboardPresetServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        match_service = MatchServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        scoreboard_service = ScoreboardServiceDB(test_db)

        preset = await preset_service.create(
            SportScoreboardPresetSchemaCreate(
                title="Cricket Preset",
                is_qtr=True,
                period_mode=SportPeriodMode.QTR,
                period_count=4,
                is_time=True,
            )
        )

        sport = await sport_service.create(SportFactoryAny.build(scoreboard_preset_id=preset.id))

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        scoreboard_with_preset = await scoreboard_service.create(
            ScoreboardSchemaCreate(
                match_id=match.id,
                use_sport_preset=True,
                is_qtr=False,
                period_mode=SportPeriodMode.PERIOD,
                period_count=5,
            )
        )

        assert scoreboard_with_preset.use_sport_preset is True

        await preset_service.update(
            preset.id,
            SportScoreboardPresetSchemaUpdate(
                is_qtr=False,
                period_mode=SportPeriodMode.HALF,
                period_count=2,
            ),
        )

        updated_with_preset = await scoreboard_service.get_by_id(scoreboard_with_preset.id)
        assert updated_with_preset.is_qtr is False
        assert updated_with_preset.period_mode == "half"
        assert updated_with_preset.period_count == 2

    async def test_preset_update_reconciles_playclock_downgrade_for_opted_in_matches(self, test_db):
        preset_service = SportScoreboardPresetServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        match_service = MatchServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        scoreboard_service = ScoreboardServiceDB(test_db)
        playclock_service = PlayClockServiceDB(test_db)

        preset = await preset_service.create(
            SportScoreboardPresetSchemaCreate(
                title="Football Preset",
                has_playclock=True,
                is_playclock=True,
            )
        )

        sport = await sport_service.create(SportFactoryAny.build(scoreboard_preset_id=preset.id))

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        scoreboard = await scoreboard_service.create(
            ScoreboardSchemaCreate(
                match_id=match.id,
                use_sport_preset=True,
                is_playclock=True,
            )
        )

        playclock = await playclock_service.create(
            PlayClockSchemaCreate(
                match_id=match.id,
                playclock=25,
                playclock_status=ClockStatus.RUNNING,
                started_at_ms=123456,
            )
        )

        await preset_service.update(
            preset.id,
            SportScoreboardPresetSchemaUpdate(
                has_playclock=False,
                is_playclock=True,
            ),
        )

        updated_scoreboard = await scoreboard_service.get_by_id(scoreboard.id)
        updated_playclock = await playclock_service.get_by_id(playclock.id)

        assert updated_scoreboard.is_playclock is False
        assert updated_playclock.playclock is None
        assert updated_playclock.playclock_status == ClockStatus.STOPPED
        assert updated_playclock.started_at_ms is None
        assert updated_playclock.version == playclock.version + 1

    async def test_preset_update_reconciles_timeouts_only_for_opted_in_matches(self, test_db):
        preset_service = SportScoreboardPresetServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        match_service = MatchServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        scoreboard_service = ScoreboardServiceDB(test_db)

        preset = await preset_service.create(
            SportScoreboardPresetSchemaCreate(
                title="Timeout Preset",
                has_timeouts=True,
            )
        )

        sport = await sport_service.create(SportFactoryAny.build(scoreboard_preset_id=preset.id))

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_c = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_d = await team_service.create(TeamFactory.build(sport_id=sport.id))

        opted_in_match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id,
                team_a_id=team_a.id,
                team_b_id=team_b.id,
            )
        )
        opted_out_match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id,
                team_a_id=team_c.id,
                team_b_id=team_d.id,
            )
        )

        opted_in_scoreboard = await scoreboard_service.create(
            ScoreboardSchemaCreate(
                match_id=opted_in_match.id,
                use_sport_preset=True,
                is_timeout_team_a=True,
                is_timeout_team_b=True,
            )
        )
        opted_out_scoreboard = await scoreboard_service.create(
            ScoreboardSchemaCreate(
                match_id=opted_out_match.id,
                use_sport_preset=False,
                is_timeout_team_a=True,
                is_timeout_team_b=True,
            )
        )

        await preset_service.update(
            preset.id,
            SportScoreboardPresetSchemaUpdate(has_timeouts=False),
        )

        updated_opted_in = await scoreboard_service.get_by_id(opted_in_scoreboard.id)
        updated_opted_out = await scoreboard_service.get_by_id(opted_out_scoreboard.id)

        assert updated_opted_in.is_timeout_team_a is False
        assert updated_opted_in.is_timeout_team_b is False
        assert updated_opted_out.is_timeout_team_a is True
        assert updated_opted_out.is_timeout_team_b is True

    async def test_preset_update_does_not_affect_opted_out_matches(self, test_db):
        preset_service = SportScoreboardPresetServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        match_service = MatchServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        scoreboard_service = ScoreboardServiceDB(test_db)

        preset = await preset_service.create(
            SportScoreboardPresetSchemaCreate(
                title="Baseball Preset",
                is_qtr=True,
                period_mode=SportPeriodMode.INNING,
                period_count=9,
                is_time=True,
            )
        )

        sport = await sport_service.create(SportFactoryAny.build(scoreboard_preset_id=preset.id))

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        scoreboard_opted_out = await scoreboard_service.create(
            ScoreboardSchemaCreate(
                match_id=match.id,
                use_sport_preset=False,
                is_qtr=False,
                period_mode=SportPeriodMode.CUSTOM,
                period_count=2,
                period_labels_json=["period.top", "period.bottom"],
                is_time=True,
            )
        )

        assert scoreboard_opted_out.use_sport_preset is False
        assert scoreboard_opted_out.is_qtr is False
        assert scoreboard_opted_out.period_mode == "custom"
        assert scoreboard_opted_out.period_count == 2
        assert scoreboard_opted_out.is_time is True

        await preset_service.update(
            preset.id,
            SportScoreboardPresetSchemaUpdate(
                is_qtr=False,
                period_mode=SportPeriodMode.HALF,
                period_count=2,
            ),
        )

        updated_opted_out = await scoreboard_service.get_by_id(scoreboard_opted_out.id)
        assert updated_opted_out.is_qtr is False
        assert updated_opted_out.period_mode == "custom"
        assert updated_opted_out.period_count == 2
        assert updated_opted_out.period_labels_json == ["period.top", "period.bottom"]
        assert updated_opted_out.is_time is True

    async def test_preset_update_propagates_to_gameclock(self, test_db):
        preset_service = SportScoreboardPresetServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        match_service = MatchServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        from src.gameclocks.db_services import GameClockServiceDB

        gameclock_service = GameClockServiceDB(test_db)

        preset = await preset_service.create(
            SportScoreboardPresetSchemaCreate(
                title="Lacrosse Preset",
                gameclock_max=720,
                direction=ClockDirection.DOWN,
                on_stop_behavior=ClockOnStopBehavior.HOLD,
            )
        )

        sport = await sport_service.create(SportFactoryAny.build(scoreboard_preset_id=preset.id))

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        gameclock = await gameclock_service.create(
            GameClockSchemaCreate(
                match_id=match.id,
                gameclock=720,
                gameclock_max=720,
                direction=ClockDirection.DOWN,
                on_stop_behavior=ClockOnStopBehavior.HOLD,
                use_sport_preset=True,
            )
        )

        assert gameclock.use_sport_preset is True
        assert gameclock.gameclock_max == 720

        await preset_service.update(
            preset.id,
            SportScoreboardPresetSchemaUpdate(
                gameclock_max=900,
                direction=ClockDirection.UP,
                on_stop_behavior=ClockOnStopBehavior.RESET,
            ),
        )

        updated_gameclock = await gameclock_service.get_by_id(gameclock.id)
        assert updated_gameclock.gameclock_max == 900
        assert updated_gameclock.direction == ClockDirection.UP
        assert updated_gameclock.on_stop_behavior == ClockOnStopBehavior.RESET

    async def test_preset_update_respects_gameclock_use_sport_preset(self, test_db):
        preset_service = SportScoreboardPresetServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        match_service = MatchServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        from src.gameclocks.db_services import GameClockServiceDB

        gameclock_service = GameClockServiceDB(test_db)

        preset = await preset_service.create(
            SportScoreboardPresetSchemaCreate(title="Handball Preset", gameclock_max=720)
        )

        sport = await sport_service.create(SportFactoryAny.build(scoreboard_preset_id=preset.id))

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        gameclock_opted_out = await gameclock_service.create(
            GameClockSchemaCreate(
                match_id=match.id,
                gameclock=600,
                gameclock_max=600,
                use_sport_preset=False,
            )
        )

        assert gameclock_opted_out.use_sport_preset is False
        assert gameclock_opted_out.gameclock_max == 600

        await preset_service.update(preset.id, SportScoreboardPresetSchemaUpdate(gameclock_max=900))

        updated_opted_out = await gameclock_service.get_by_id(gameclock_opted_out.id)
        assert updated_opted_out.gameclock_max == 600

    async def test_preset_update_propagates_cumulative_effective_max_by_period(self, test_db):
        preset_service = SportScoreboardPresetServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        match_service = MatchServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        from src.gameclocks.db_services import GameClockServiceDB

        gameclock_service = GameClockServiceDB(test_db)
        matchdata_service = MatchDataServiceDB(test_db)

        preset = await preset_service.create(
            SportScoreboardPresetSchemaCreate(
                title="Soccer Preset",
                gameclock_max=900,
                period_clock_variant=PeriodClockVariant.PER_PERIOD,
            )
        )

        sport = await sport_service.create(SportFactoryAny.build(scoreboard_preset_id=preset.id))

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id,
                team_a_id=team_a.id,
                team_b_id=team_b.id,
            )
        )

        gameclock = await gameclock_service.create(
            GameClockSchemaCreate(
                match_id=match.id,
                gameclock=1200,
                gameclock_time_remaining=1200,
                gameclock_max=900,
                use_sport_preset=True,
            )
        )

        await matchdata_service.create(
            MatchDataSchemaCreate(
                match_id=match.id,
                qtr="2nd",
                period_key="period.2",
            )
        )

        await preset_service.update(
            preset.id,
            SportScoreboardPresetSchemaUpdate(
                period_clock_variant=PeriodClockVariant.CUMULATIVE,
            ),
        )

        updated_gameclock = await gameclock_service.get_by_id(gameclock.id)
        assert updated_gameclock is not None
        assert updated_gameclock.gameclock_max == 1800
        assert updated_gameclock.gameclock == 1200

    async def test_preset_with_multiple_sports(self, test_db):
        preset_service = SportScoreboardPresetServiceDB(test_db)
        sport_service = SportServiceDB(test_db)

        preset = await preset_service.create(
            SportScoreboardPresetSchemaCreate(title="Multi-Sport Preset")
        )

        await sport_service.create(
            SportFactoryAny.build(scoreboard_preset_id=preset.id, title="Sport 1")
        )
        await sport_service.create(
            SportFactoryAny.build(scoreboard_preset_id=preset.id, title="Sport 2")
        )
        await sport_service.create(
            SportFactoryAny.build(scoreboard_preset_id=preset.id, title="Sport 3")
        )

        sports = await preset_service.get_sports_by_preset(preset.id)

        assert len(sports) == 3

    async def test_preset_with_direction_up(self, test_db):
        service = SportScoreboardPresetServiceDB(test_db)
        preset_data = SportScoreboardPresetSchemaCreate(
            title="Count-up Preset",
            direction=ClockDirection.UP,
            gameclock_max=1000,
        )

        result = await service.create(preset_data)

        assert result.direction == ClockDirection.UP
        assert result.gameclock_max == 1000

    async def test_preset_with_on_stop_behavior_reset(self, test_db):
        service = SportScoreboardPresetServiceDB(test_db)
        preset_data = SportScoreboardPresetSchemaCreate(
            title="Reset Preset",
            on_stop_behavior=ClockOnStopBehavior.RESET,
        )

        result = await service.create(preset_data)

        assert result.on_stop_behavior == ClockOnStopBehavior.RESET

    async def test_update_preset_partial_fields(self, test_db):
        service = SportScoreboardPresetServiceDB(test_db)
        preset_data = SportScoreboardPresetSchemaCreate(
            title="Full Preset",
            gameclock_max=720,
            period_clock_variant=PeriodClockVariant.PER_PERIOD,
            direction=ClockDirection.DOWN,
            on_stop_behavior=ClockOnStopBehavior.HOLD,
            is_qtr=True,
            is_time=True,
            is_playclock=True,
            is_downdistance=True,
            has_timeouts=False,
            has_playclock=False,
            period_mode=SportPeriodMode.CUSTOM,
            period_count=2,
            period_labels_json=["period.q1", "period.q2"],
            default_playclock_seconds=40,
        )

        created = await service.create(preset_data)
        update_data = SportScoreboardPresetSchemaUpdate(gameclock_max=900)

        updated = await service.update(created.id, update_data)

        assert updated.title == "Full Preset"
        assert updated.gameclock_max == 900
        assert updated.period_clock_variant == PeriodClockVariant.PER_PERIOD
        assert updated.direction == ClockDirection.DOWN
        assert updated.on_stop_behavior == ClockOnStopBehavior.HOLD
        assert updated.is_qtr is True
        assert updated.is_time is True
        assert updated.is_playclock is True
        assert updated.is_downdistance is True
        assert updated.has_timeouts is False
        assert updated.has_playclock is False
        assert updated.period_mode == "custom"
        assert updated.period_count == 2
        assert updated.period_labels_json == ["period.q1", "period.q2"]
        assert updated.default_playclock_seconds == 40

    async def test_update_preset_with_min_initial_time_mode(self, test_db):
        service = SportScoreboardPresetServiceDB(test_db)
        preset_data = SportScoreboardPresetSchemaCreate(title="Initial Mode Update Preset")

        created = await service.create(preset_data)
        update_data = SportScoreboardPresetSchemaUpdate(
            initial_time_mode=InitialTimeMode.MIN,
            initial_time_min_seconds=90,
        )

        updated = await service.update(created.id, update_data)

        assert updated.initial_time_mode == InitialTimeMode.MIN
        assert updated.initial_time_min_seconds == 90

    async def test_update_preset_period_clock_variant(self, test_db):
        service = SportScoreboardPresetServiceDB(test_db)
        created = await service.create(
            SportScoreboardPresetSchemaCreate(title="Soccer Variant Preset")
        )

        updated = await service.update(
            created.id,
            SportScoreboardPresetSchemaUpdate(
                period_clock_variant=PeriodClockVariant.CUMULATIVE,
            ),
        )

        assert updated.period_clock_variant == PeriodClockVariant.CUMULATIVE

    async def test_delete_preset_unlinks_from_sports(self, test_db):
        preset_service = SportScoreboardPresetServiceDB(test_db)
        sport_service = SportServiceDB(test_db)

        preset = await preset_service.create(
            SportScoreboardPresetSchemaCreate(title="Deletable Preset")
        )

        sport = await sport_service.create(SportFactoryAny.build(scoreboard_preset_id=preset.id))

        assert sport.scoreboard_preset_id == preset.id

        await preset_service.delete(preset.id)

        updated_sport = await sport_service.get_by_id(sport.id)
        assert updated_sport is not None
        assert updated_sport.scoreboard_preset_id is None
