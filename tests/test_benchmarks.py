"""
Performance benchmarks for critical service operations.

Run benchmarks with:
    pytest tests/test_benchmarks.py -m benchmark

Run benchmarks with coverage:
    pytest tests/test_benchmarks.py -m benchmark --cov=src --cov-report=html

Compare benchmarks with baseline:
    pytest tests/test_benchmarks.py -m benchmark --benchmark-only --benchmark-compare
"""

from datetime import datetime

import pytest

from tests.factories import (
    MatchFactory,
    SeasonFactoryAny,
    TournamentFactory,
)


@pytest.mark.benchmark
@pytest.mark.asyncio
class TestSeasonServicePerformance:
    """Benchmark tests for SeasonService operations."""

    async def test_create_season_single(self, test_season_service, benchmark):
        """Benchmark single season creation."""
        season_data = SeasonFactoryAny.build(year=2999)

        async def create_season():
            return await test_season_service.create(season_data)

        result = await benchmark.pedantic(create_season)
        assert result is not None

    async def test_create_season_bulk(self, test_season_service, benchmark):
        """Benchmark bulk season creation (100 seasons)."""
        seasons_data = [SeasonFactoryAny.build(year=2900 + i) for i in range(100)]

        async def create_bulk_seasons():
            results = []
            for season_data in seasons_data:
                result = await test_season_service.create(season_data)
                results.append(result)
            return results

        results = await benchmark.pedantic(create_bulk_seasons)
        assert len(results) == 100

    async def test_get_all_seasons(self, test_season_service, test_db, benchmark):
        """Benchmark fetching all seasons from database."""
        for i in range(50):
            season_data = SeasonFactoryAny.build(year=1950 + i)
            await test_season_service.create(season_data)

        async def get_all():
            return await test_season_service.get_all_elements()

        results = await benchmark.pedantic(get_all)
        assert len(results) >= 50

    async def test_get_season_by_id(self, test_season_service, season, benchmark):
        """Benchmark fetching season by ID."""

        async def get_by_id():
            return await test_season_service.get_by_id(season.id)

        result = await benchmark.pedantic(get_by_id)
        assert result.id == season.id


@pytest.mark.benchmark
@pytest.mark.asyncio
class TestTournamentServicePerformance:
    """Benchmark tests for TournamentService operations."""

    async def test_create_tournament_single(
        self, test_tournament_service, sport, season, benchmark
    ):
        """Benchmark single tournament creation."""
        tournament_data = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, title=f"Test Tournament {5000}"
        )

        async def create_tournament():
            return await test_tournament_service.create(tournament_data)

        result = await benchmark.pedantic(create_tournament)
        assert result is not None

    async def test_create_tournament_bulk(self, test_tournament_service, sport, season, benchmark):
        """Benchmark bulk tournament creation (100 tournaments)."""
        tournaments_data = [
            TournamentFactory.build(
                sport_id=sport.id,
                season_id=season.id,
                title=f"Tournament {i}",
            )
            for i in range(100)
        ]

        async def create_bulk_tournaments():
            results = []
            for tournament_data in tournaments_data:
                result = await test_tournament_service.create(tournament_data)
                results.append(result)
            return results

        results = await benchmark.pedantic(create_bulk_tournaments)
        assert len(results) == 100

    async def test_get_all_tournaments(self, test_tournament_service, tournament, benchmark):
        """Benchmark fetching all tournaments from database."""

        async def get_all():
            return await test_tournament_service.get_all_elements()

        results = await benchmark.pedantic(get_all)
        assert len(results) >= 1

    async def test_get_tournament_by_id(self, test_tournament_service, tournament, benchmark):
        """Benchmark fetching tournament by ID."""

        async def get_by_id():
            return await test_tournament_service.get_by_id(tournament.id)

        result = await benchmark.pedantic(get_by_id)
        assert result.id == tournament.id


@pytest.mark.benchmark
@pytest.mark.asyncio
class TestMatchStatsServicePerformance:
    """Benchmark tests for MatchStatsService operations."""

    async def test_calculate_team_stats_single(self, test_db, sport, season, teams_data, benchmark):
        """Benchmark single team stats calculation."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=999
        )

        from src.football_events.db_services import FootballEventServiceDB
        from src.football_events.schemas import FootballEventSchemaCreate
        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=600,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        event_service = FootballEventServiceDB(test_db)

        for i in range(10):
            event = FootballEventSchemaCreate(
                match_id=match.id,
                event_number=i + 1,
                event_qtr=1,
                ball_on=25 + i * 5,
                ball_moved_to=30 + i * 5,
                offense_team=team_a.id,
                play_type="run",
                play_result="run",
            )
            await event_service.create(event)

        from src.matches.stats_service import MatchStatsServiceDB

        stats_service = MatchStatsServiceDB(test_db)

        async def calculate_stats():
            return await stats_service.calculate_team_stats(match.id, team_a.id)

        result = await benchmark.pedantic(calculate_stats)
        assert result is not None

    async def test_calculate_team_stats_multiple_events(
        self, test_db, sport, season, teams_data, benchmark
    ):
        """Benchmark team stats calculation with 100 events."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=998
        )

        from src.football_events.db_services import FootballEventServiceDB
        from src.football_events.schemas import FootballEventSchemaCreate
        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=601,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        event_service = FootballEventServiceDB(test_db)

        for i in range(100):
            event = FootballEventSchemaCreate(
                match_id=match.id,
                event_number=i + 1,
                event_qtr=1,
                ball_on=25,
                ball_moved_to=35,
                offense_team=team_a.id,
                play_type="run",
                play_result="run",
            )
            await event_service.create(event)

        from src.matches.stats_service import MatchStatsServiceDB

        stats_service = MatchStatsServiceDB(test_db)

        async def calculate_stats():
            return await stats_service.calculate_team_stats(match.id, team_a.id)

        result = await benchmark.pedantic(calculate_stats)
        assert result is not None

    async def test_get_match_with_cached_stats(self, test_db, sport, season, teams_data, benchmark):
        """Benchmark full match stats retrieval with caching."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=997
        )

        from src.matches.db_services import MatchServiceDB
        from src.tournaments.db_services import TournamentServiceDB

        tournament_service = TournamentServiceDB(test_db)
        created_tournament = await tournament_service.create(tournament_factory)

        match_factory = MatchFactory.build(
            match_eesl_id=602,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        from src.matches.stats_service import MatchStatsServiceDB

        stats_service = MatchStatsServiceDB(test_db)

        async def get_cached_stats():
            return await stats_service.get_match_with_cached_stats(match.id)

        result = await benchmark.pedantic(get_cached_stats)
        assert result is not None
