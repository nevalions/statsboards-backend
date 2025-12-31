"""
Performance benchmarks for critical service operations.

Run benchmarks with:
    pytest tests/test_benchmarks.py -m benchmark

Run benchmarks with coverage:
    pytest tests/test_benchmarks.py -m benchmark --cov=src --cov-report=html

Compare benchmarks with baseline:
    pytest tests/test_benchmarks.py -m benchmark --benchmark-only --benchmark-compare
"""

import pytest
from tests.factories import SeasonFactoryAny, TournamentFactory


@pytest.mark.benchmark
@pytest.mark.asyncio
class TestSeasonServicePerformance:
    """Benchmark tests for SeasonService operations."""

    async def test_create_season_single(
        self, test_season_service, benchmark
    ):
        """Benchmark single season creation."""
        season_data = SeasonFactoryAny.build()

        async def create_season():
            return await test_season_service.create(season_data)

        result = benchmark(create_season)
        assert result is not None

    async def test_create_season_bulk(self, test_season_service, benchmark):
        """Benchmark bulk season creation (100 seasons)."""
        seasons_data = [SeasonFactoryAny.build() for _ in range(100)]

        async def create_bulk_seasons():
            results = []
            for season_data in seasons_data:
                result = await test_season_service.create(season_data)
                results.append(result)
            return results

        results = benchmark(create_bulk_seasons)
        assert len(results) == 100

    async def test_get_all_seasons(
        self, test_season_service, test_db, benchmark
    ):
        """Benchmark fetching all seasons from database."""
        for _ in range(50):
            season_data = SeasonFactoryAny.build()
            await test_season_service.create(season_data)

        async def get_all():
            return await test_season_service.get_all()

        results = benchmark(get_all)
        assert len(results) >= 50

    async def test_get_season_by_id(
        self, test_season_service, season, benchmark
    ):
        """Benchmark fetching season by ID."""
        async def get_by_id():
            return await test_season_service.get_by_id(season.id)

        result = benchmark(get_by_id)
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
            sport_id=sport.id, season_id=season.id
        )

        async def create_tournament():
            return await test_tournament_service.create(tournament_data)

        result = benchmark(create_tournament)
        assert result is not None

    async def test_create_tournament_bulk(
        self, test_tournament_service, sport, season, benchmark
    ):
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

        results = benchmark(create_bulk_tournaments)
        assert len(results) == 100

    async def test_get_all_tournaments(
        self, test_tournament_service, tournament, benchmark
    ):
        """Benchmark fetching all tournaments from database."""
        async def get_all():
            return await test_tournament_service.get_all()

        results = benchmark(get_all)
        assert len(results) >= 1

    async def test_get_tournament_by_id(
        self, test_tournament_service, tournament, benchmark
    ):
        """Benchmark fetching tournament by ID."""
        async def get_by_id():
            return await test_tournament_service.get_by_id(tournament.id)

        result = benchmark(get_by_id)
        assert result.id == tournament.id
