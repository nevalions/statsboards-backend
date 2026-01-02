"""
Additional focused tests for MatchStatsServiceDB.

These tests extend base tests with specific stat calculations.
"""

from datetime import datetime

import pytest

from src.matches.stats_service import MatchStatsServiceDB
from tests.factories import (
    MatchFactory,
    TournamentFactory,
)


@pytest.mark.asyncio
class TestMatchStatsServiceDBFocused:
    """Focused tests for specific stat calculation scenarios."""

    async def test_cache_invalidation_on_event_update(self, test_db, sport, season, teams_data):
        """Test cache recalculation when events are updated."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=901
        )

        from src.football_events.db_services import FootballEventServiceDB
        from src.football_events.schemas import FootballEventSchemaCreate
        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=101,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        stats_service = MatchStatsServiceDB(test_db)
        stats1 = await stats_service.get_match_with_cached_stats(match.id)

        event_service = FootballEventServiceDB(test_db)
        event = FootballEventSchemaCreate(
            match_id=match.id,
            event_number=1,
            event_qtr=1,
            ball_on=25,
            ball_moved_to=35,
            offense_team=team_a.id,
            play_type="run",
            play_result="run",
        )
        await event_service.create(event)

        stats2 = await stats_service.get_match_with_cached_stats(match.id)

        assert stats1["match_id"] == stats2["match_id"]
        assert match.id in stats_service._cache

    async def test_calculate_multiple_events_cumulative(self, test_db, sport, season, teams_data):
        """Test that multiple events accumulate correctly."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=902
        )

        from src.football_events.db_services import FootballEventServiceDB
        from src.football_events.schemas import FootballEventSchemaCreate
        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=102,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        event_service = FootballEventServiceDB(test_db)

        event1 = FootballEventSchemaCreate(
            match_id=match.id,
            event_number=1,
            event_qtr=1,
            ball_on=25,
            ball_moved_to=35,
            offense_team=team_a.id,
            play_type="run",
            play_result="run",
        )
        event2 = FootballEventSchemaCreate(
            match_id=match.id,
            event_number=2,
            event_qtr=1,
            ball_on=35,
            ball_moved_to=50,
            offense_team=team_a.id,
            play_type="pass",
            play_result="completed",
        )

        await event_service.create(event1)
        await event_service.create(event2)

        stats_service = MatchStatsServiceDB(test_db)
        stats = await stats_service.calculate_team_stats(match.id, team_a.id)

        assert stats["run_yards"] == 10
        assert stats["pass_yards"] == 15
        assert stats["offence_yards"] == 25
        assert stats["run_att"] == 1
        assert stats["pass_att"] == 1

    async def test_calculate_zero_events(self, test_db, sport, season, teams_data):
        """Test calculation with no events returns zero stats."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=903
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=103,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        stats_service = MatchStatsServiceDB(test_db)
        stats = await stats_service.calculate_team_stats(match.id, team_a.id)

        assert stats["offence_yards"] == 0
        assert stats["pass_att"] == 0
        assert stats["run_att"] == 0
        assert stats["pass_yards"] == 0
        assert stats["run_yards"] == 0
        assert stats["lost_yards"] == 0
        assert stats["turnovers"] == 0

    async def test_calculate_opponent_stats(self, test_db, sport, season, teams_data):
        """Test that opponent stats are calculated separately."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=904
        )

        from src.football_events.db_services import FootballEventServiceDB
        from src.football_events.schemas import FootballEventSchemaCreate
        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=104,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        event_service = FootballEventServiceDB(test_db)

        event = FootballEventSchemaCreate(
            match_id=match.id,
            event_number=1,
            event_qtr=1,
            ball_on=25,
            ball_moved_to=35,
            offense_team=team_a.id,
            play_type="run",
            play_result="run",
        )

        await event_service.create(event)

        stats_service = MatchStatsServiceDB(test_db)
        stats_a = await stats_service.calculate_team_stats(match.id, team_a.id)
        stats_b = await stats_service.calculate_team_stats(match.id, team_b.id)

        assert stats_a["offence_yards"] == 10
        assert stats_a["run_att"] == 1
        assert stats_b["offence_yards"] == 0
        assert stats_b["run_att"] == 0

    async def test_calculate_offense_stats(self, test_db, sport, season, teams_data):
        """Test offense stats calculation."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=905
        )

        from src.football_events.db_services import FootballEventServiceDB
        from src.football_events.schemas import FootballEventSchemaCreate
        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=105,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        event_service = FootballEventServiceDB(test_db)

        event = FootballEventSchemaCreate(
            match_id=match.id,
            event_number=1,
            event_qtr=1,
            ball_on=25,
            ball_moved_to=40,
            offense_team=team_a.id,
            play_type="pass",
            play_result="completed",
        )

        await event_service.create(event)

        stats_service = MatchStatsServiceDB(test_db)
        offense_stats = await stats_service.calculate_offense_stats(match.id, team_a.id)

        assert len(offense_stats) == 0

    async def test_calculate_defense_stats(self, test_db, sport, season, teams_data):
        """Test defense stats calculation."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=906
        )

        from src.football_events.db_services import FootballEventServiceDB
        from src.football_events.schemas import FootballEventSchemaCreate
        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=106,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        event_service = FootballEventServiceDB(test_db)

        event = FootballEventSchemaCreate(
            match_id=match.id,
            event_number=1,
            event_qtr=1,
            ball_on=25,
            ball_moved_to=35,
            offense_team=team_b.id,
            play_type="run",
            play_result="run",
        )

        await event_service.create(event)

        stats_service = MatchStatsServiceDB(test_db)
        defense_stats = await stats_service.calculate_defense_stats(match.id, team_a.id)

        assert len(defense_stats) == 0
