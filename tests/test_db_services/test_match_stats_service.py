from datetime import datetime

import pytest

from src.matches.stats_service import MatchStatsServiceDB
from tests.factories import (
    MatchFactory,
    TournamentFactory,
)


@pytest.mark.asyncio
class TestMatchStatsServiceDB:
    """Test MatchStatsServiceDB functionality."""

    async def test_calculate_team_stats_empty_events(self, test_db, sport, season, teams_data):
        """Test calculating team stats with no events."""
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

        stats_service = MatchStatsServiceDB(test_db)
        stats = await stats_service.calculate_team_stats(match.id, team_a.id)

        assert stats is not None
        assert stats["id"] == team_a.id
        assert stats["offence_yards"] == 0
        assert stats["pass_att"] == 0
        assert stats["run_att"] == 0
        assert stats["pass_yards"] == 0
        assert stats["run_yards"] == 0
        assert stats["lost_yards"] == 0
        assert stats["flag_yards"] == 0
        assert stats["turnovers"] == 0

    async def test_calculate_team_stats_with_run_play(self, test_db, sport, season, teams_data):
        """Test calculating team stats with run plays."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=900
        )

        from src.football_events.db_services import FootballEventServiceDB
        from src.football_events.schemas import FootballEventSchemaCreate
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
        stats = await stats_service.calculate_team_stats(match.id, team_a.id)

        assert stats is not None
        assert stats["id"] == team_a.id
        assert stats["run_yards"] == 10
        assert stats["run_att"] == 1
        assert stats["offence_yards"] == 10

    async def test_calculate_team_stats_with_pass_play(self, test_db, sport, season, teams_data):
        """Test calculating team stats with pass plays."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=900
        )

        from src.football_events.db_services import FootballEventServiceDB
        from src.football_events.schemas import FootballEventSchemaCreate
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
        stats = await stats_service.calculate_team_stats(match.id, team_a.id)

        assert stats is not None
        assert stats["id"] == team_a.id
        assert stats["pass_yards"] == 15
        assert stats["pass_att"] == 1
        assert stats["offence_yards"] == 15

    async def test_get_match_with_cached_stats(self, test_db, sport, season, teams_data):
        """Test getting match with cached stats."""
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

        stats_service = MatchStatsServiceDB(test_db)
        stats = await stats_service.get_match_with_cached_stats(match.id)

        assert stats is not None
        assert "match_id" in stats
        assert "team_a" in stats
        assert "team_b" in stats
        assert stats["match_id"] == match.id
        assert stats["team_a"]["id"] == team_a.id
        assert stats["team_b"]["id"] == team_b.id

    async def test_invalidate_cache(self, test_db, sport, season, teams_data):
        """Test cache invalidation."""
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

        stats_service = MatchStatsServiceDB(test_db)

        await stats_service.get_match_with_cached_stats(match.id)
        assert match.id in stats_service._cache

        stats_service.invalidate_cache(match.id)
        assert match.id not in stats_service._cache
