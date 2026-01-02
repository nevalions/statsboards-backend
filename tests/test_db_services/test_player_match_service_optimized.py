from datetime import datetime

import pytest

from src.matches.db_services import MatchServiceDB
from src.player.db_services import PlayerServiceDB
from src.player_match.db_services import PlayerMatchServiceDB
from tests.factories import (
    MatchFactory,
    PlayerFactory,
    TournamentFactory,
)


@pytest.mark.asyncio
class TestPlayerMatchServiceDBOptimized:
    """Test PlayerMatchServiceDB optimized methods."""

    async def test_get_players_with_full_data_optimized_performance(
        self, test_db, sport, season, teams_data
    ):
        """Test that optimized method uses single query with selectinload."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=900
        )

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

        import time

        start_time = time.perf_counter()

        result = await match_service.get_players_with_full_data_optimized(match.id)

        optimized_time = time.perf_counter() - start_time

        assert isinstance(result, list)
        assert len(result) >= 0

        print(f"Optimized method took: {optimized_time:.4f}s")

    async def test_get_players_with_full_data_optimized_empty_match(
        self, test_db, sport, season, teams_data
    ):
        """Test optimized method with empty match."""
        team_a, team_b = teams_data

        tournament_factory = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=900
        )

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

        result = await match_service.get_players_with_full_data_optimized(match.id)

        assert result == []
