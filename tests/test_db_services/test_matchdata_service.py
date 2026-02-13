import pytest

from src.core.enums import ClockDirection, GameStatus, PeriodClockVariant
from src.gameclocks.db_services import GameClockServiceDB
from src.gameclocks.schemas import GameClockSchemaCreate
from src.helpers.fetch_helpers import fetch_gameclock
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
class TestMatchDataServiceDB:
    async def _create_match_with_preset(
        self,
        test_db,
        *,
        period_clock_variant: PeriodClockVariant,
    ):
        preset_service = SportScoreboardPresetServiceDB(test_db)
        preset = await preset_service.create(
            SportScoreboardPresetSchemaCreate(
                title="Preset with variant",
                gameclock_max=2700,
                period_clock_variant=period_clock_variant,
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
                tournament_id=tournament.id,
                team_a_id=team_a.id,
                team_b_id=team_b.id,
            )
        )

        return match

    async def test_create_matchdata(self, test_db):
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

        matchdata_service = MatchDataServiceDB(test_db)
        matchdata = MatchDataSchemaCreate(
            match_id=match.id,
            field_length=92,
            game_status=GameStatus.IN_PROGRESS,
            score_team_a=0,
            score_team_b=0,
            qtr="1st",
            period_key="period.1",
        )

        result = await matchdata_service.create(matchdata)

        assert result is not None
        assert result.id is not None
        assert result.match_id == match.id
        assert result.game_status == "in-progress"
        assert result.period_key == "period.1"

    async def test_update_matchdata(self, test_db):
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

        matchdata_service = MatchDataServiceDB(test_db)
        matchdata = MatchDataSchemaCreate(match_id=match.id, score_team_a=0, score_team_b=0)

        created = await matchdata_service.create(matchdata)
        update_data = MatchDataSchemaUpdate(
            score_team_a=7,
            score_team_b=3,
            qtr="2nd",
            period_key="period.2",
        )

        updated = await matchdata_service.update(created.id, update_data)

        assert updated.score_team_a == 7
        assert updated.score_team_b == 3
        assert updated.qtr == "2nd"
        assert updated.period_key == "period.2"

    async def test_get_match_data_by_match_id(self, test_db):
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

        matchdata_service = MatchDataServiceDB(test_db)
        matchdata = MatchDataSchemaCreate(match_id=match.id, score_team_a=0, score_team_b=0)

        created = await matchdata_service.create(matchdata)
        result = await matchdata_service.get_match_data_by_match_id(match.id)

        assert result is not None
        assert result.id == created.id

    async def test_get_match_data_by_match_id_not_found(self, test_db):
        matchdata_service = MatchDataServiceDB(test_db)
        result = await matchdata_service.get_match_data_by_match_id(99999)

        assert result is None

    async def test_get_match_data_by_match_id_empty(self, test_db):
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

        matchdata_service = MatchDataServiceDB(test_db)
        result = await matchdata_service.get_match_data_by_match_id(match.id)

        assert result is None

    async def test_update_matchdata_recalculates_gameclock_max_for_cumulative_periods(
        self, test_db
    ):
        match = await self._create_match_with_preset(
            test_db,
            period_clock_variant=PeriodClockVariant.CUMULATIVE,
        )

        gameclock_service = GameClockServiceDB(test_db)
        gameclock = await gameclock_service.create(
            GameClockSchemaCreate(
                match_id=match.id,
                gameclock=2700,
                gameclock_time_remaining=2700,
                gameclock_max=2700,
                direction=ClockDirection.UP,
                use_sport_preset=True,
            )
        )

        matchdata_service = MatchDataServiceDB(test_db)
        matchdata = await matchdata_service.create(
            MatchDataSchemaCreate(match_id=match.id, qtr="1st", period_key="period.1")
        )

        await matchdata_service.update(
            matchdata.id,
            MatchDataSchemaUpdate(qtr="2nd", period_key="period.2"),
        )

        updated_gameclock = await gameclock_service.get_by_id(gameclock.id)
        assert updated_gameclock is not None
        assert updated_gameclock.gameclock_max == 5400

    async def test_update_matchdata_keeps_base_max_for_per_period_variant(self, test_db):
        match = await self._create_match_with_preset(
            test_db,
            period_clock_variant=PeriodClockVariant.PER_PERIOD,
        )

        gameclock_service = GameClockServiceDB(test_db)
        gameclock = await gameclock_service.create(
            GameClockSchemaCreate(
                match_id=match.id,
                gameclock=2700,
                gameclock_time_remaining=2700,
                gameclock_max=2700,
                direction=ClockDirection.UP,
                use_sport_preset=True,
            )
        )

        matchdata_service = MatchDataServiceDB(test_db)
        matchdata = await matchdata_service.create(
            MatchDataSchemaCreate(match_id=match.id, qtr="1st", period_key="period.1")
        )

        await matchdata_service.update(
            matchdata.id,
            MatchDataSchemaUpdate(qtr="2nd", period_key="period.2"),
        )

        updated_gameclock = await gameclock_service.get_by_id(gameclock.id)
        assert updated_gameclock is not None
        assert updated_gameclock.gameclock_max == 2700

    async def test_update_matchdata_does_not_change_gameclock_when_opted_out(self, test_db):
        match = await self._create_match_with_preset(
            test_db,
            period_clock_variant=PeriodClockVariant.CUMULATIVE,
        )

        gameclock_service = GameClockServiceDB(test_db)
        gameclock = await gameclock_service.create(
            GameClockSchemaCreate(
                match_id=match.id,
                gameclock=2700,
                gameclock_time_remaining=2700,
                gameclock_max=2700,
                direction=ClockDirection.UP,
                use_sport_preset=False,
            )
        )

        matchdata_service = MatchDataServiceDB(test_db)
        matchdata = await matchdata_service.create(
            MatchDataSchemaCreate(match_id=match.id, qtr="1st", period_key="period.1")
        )

        await matchdata_service.update(
            matchdata.id,
            MatchDataSchemaUpdate(qtr="2nd", period_key="period.2"),
        )

        updated_gameclock = await gameclock_service.get_by_id(gameclock.id)
        assert updated_gameclock is not None
        assert updated_gameclock.gameclock_max == 2700

    async def test_fetch_gameclock_bootstrap_uses_cumulative_period_max(self, test_db):
        match = await self._create_match_with_preset(
            test_db,
            period_clock_variant=PeriodClockVariant.CUMULATIVE,
        )

        matchdata_service = MatchDataServiceDB(test_db)
        await matchdata_service.create(
            MatchDataSchemaCreate(match_id=match.id, qtr="2nd", period_key="period.2")
        )

        result = await fetch_gameclock(match.id, database=test_db)

        assert result is not None
        assert result["gameclock"] is not None
        assert result["gameclock"]["gameclock_max"] == 5400
        assert result["gameclock"]["gameclock"] == 5400
