import pytest
from pydantic import ValidationError

from src.core.enums import ClockDirection, ClockOnStopBehavior, SportPeriodMode
from src.gameclocks.schemas import GameClockSchemaCreate
from src.matches.db_services import MatchServiceDB
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
            period_labels_json=None,
            default_playclock_seconds=30,
        )

        result = await service.create(preset_data)

        assert result is not None
        assert result.id is not None
        assert result.title == "Basketball Preset"
        assert result.gameclock_max == 720
        assert result.direction == ClockDirection.DOWN
        assert result.on_stop_behavior == ClockOnStopBehavior.HOLD
        assert result.is_qtr is True
        assert result.is_time is True
        assert result.is_playclock is True
        assert result.is_downdistance is False
        assert result.has_timeouts is True
        assert result.has_playclock is True
        assert result.period_mode == "qtr"
        assert result.period_labels_json is None
        assert result.default_playclock_seconds == 30

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
        assert result.period_labels_json is None
        assert result.default_playclock_seconds is None

    async def test_update_preset(self, test_db):
        service = SportScoreboardPresetServiceDB(test_db)
        preset_data = SportScoreboardPresetSchemaCreate(title="Soccer Preset")

        created = await service.create(preset_data)
        update_data = SportScoreboardPresetSchemaUpdate(
            title="Soccer Preset Updated",
            gameclock_max=900,
            direction=ClockDirection.UP,
            has_timeouts=False,
            has_playclock=False,
            period_mode=SportPeriodMode.CUSTOM,
            period_labels_json=["period.leg_1", "period.leg_2"],
            default_playclock_seconds=25,
        )

        updated = await service.update(created.id, update_data)

        assert updated.title == "Soccer Preset Updated"
        assert updated.gameclock_max == 900
        assert updated.direction == ClockDirection.UP
        assert updated.has_timeouts is False
        assert updated.has_playclock is False
        assert updated.period_mode == "custom"
        assert updated.period_labels_json == ["period.leg_1", "period.leg_2"]
        assert updated.default_playclock_seconds == 25

    async def test_create_preset_rejects_non_machine_period_labels(self, test_db):
        _ = SportScoreboardPresetServiceDB(test_db)

        with pytest.raises(ValidationError):
            SportScoreboardPresetSchemaCreate(
                title="Invalid Labels",
                period_mode=SportPeriodMode.CUSTOM,
                period_labels_json=["Leg 1", "тайм 2"],
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
                is_time=False,
                is_playclock=False,
                is_downdistance=False,
            ),
        )

        updated_scoreboard = await scoreboard_service.get_by_id(scoreboard.id)
        assert updated_scoreboard.is_qtr is False
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
            ScoreboardSchemaCreate(match_id=match.id, use_sport_preset=True, is_qtr=False)
        )

        assert scoreboard_with_preset.use_sport_preset is True

        await preset_service.update(preset.id, SportScoreboardPresetSchemaUpdate(is_qtr=False))

        updated_with_preset = await scoreboard_service.get_by_id(scoreboard_with_preset.id)
        assert updated_with_preset.is_qtr is False

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
                is_time=True,
            )
        )

        assert scoreboard_opted_out.use_sport_preset is False
        assert scoreboard_opted_out.is_qtr is False
        assert scoreboard_opted_out.is_time is True

        await preset_service.update(preset.id, SportScoreboardPresetSchemaUpdate(is_qtr=False))

        updated_opted_out = await scoreboard_service.get_by_id(scoreboard_opted_out.id)
        assert updated_opted_out.is_qtr is False
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
            direction=ClockDirection.DOWN,
            on_stop_behavior=ClockOnStopBehavior.HOLD,
            is_qtr=True,
            is_time=True,
            is_playclock=True,
            is_downdistance=True,
            has_timeouts=False,
            has_playclock=False,
            period_mode=SportPeriodMode.CUSTOM,
            period_labels_json=["period.q1", "period.q2"],
            default_playclock_seconds=40,
        )

        created = await service.create(preset_data)
        update_data = SportScoreboardPresetSchemaUpdate(gameclock_max=900)

        updated = await service.update(created.id, update_data)

        assert updated.title == "Full Preset"
        assert updated.gameclock_max == 900
        assert updated.direction == ClockDirection.DOWN
        assert updated.on_stop_behavior == ClockOnStopBehavior.HOLD
        assert updated.is_qtr is True
        assert updated.is_time is True
        assert updated.is_playclock is True
        assert updated.is_downdistance is True
        assert updated.has_timeouts is False
        assert updated.has_playclock is False
        assert updated.period_mode == "custom"
        assert updated.period_labels_json == ["period.q1", "period.q2"]
        assert updated.default_playclock_seconds == 40

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
