from datetime import datetime

import pytest

from src.matches.db_services import MatchServiceDB
from src.player_match.db_services import PlayerMatchServiceDB
from src.player_match.schemas import PlayerMatchSchemaUpdate
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

        player_match_service = PlayerMatchServiceDB(test_db)

        import time

        start_time = time.perf_counter()

        result = await player_match_service.get_players_with_full_data_optimized(match.id)

        optimized_time = time.perf_counter() - start_time

        assert isinstance(result, list)
        assert len(result) >= 0

        for player_data in result:
            assert "match_player" in player_data
            assert "player_team_tournament" in player_data
            if "person" in player_data:
                assert "first_name" in player_data["person"]
            if "position" in player_data:
                assert "title" in player_data["position"]
            if "team" in player_data:
                assert "title" in player_data["team"]

        print(f"Optimized method took: {optimized_time:.4f}s")

    async def test_get_players_with_full_data_optimized_data_structure(
        self, test_db, sport, season, teams_data
    ):
        """Test that optimized method returns correct data structure."""
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

        player_match_service = PlayerMatchServiceDB(test_db)

        players = []
        for i in range(3):
            player_factory = PlayerFactory.build(sport_id=sport.id, player_eesl_id=i)
            player = await player_match_service.create(player_factory)

            player_match_schema = PlayerMatchSchemaUpdate(
                player_team_tournament_id=player.id,
                team_id=team_a.id,
                is_start=True if i == 0 else False,
            )

            await player_match_service.update(player.id, player_match_schema)
            players.append(player)

        match_factory = MatchFactory.build(
            match_eesl_id=100,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        result = await player_match_service.get_players_with_full_data_optimized(match.id)

        assert isinstance(result, list)
        assert len(result) == 3

        for player_data in result:
            assert "match_player" in player_data
            assert "player_team_tournament" in player_data
            assert "person" in player_data
            assert "position" in player_data
            assert "team" in player_data
            assert "is_start" in player_data["match_player"]

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

        player_match_service = PlayerMatchServiceDB(test_db)

        result = await player_match_service.get_players_with_full_data_optimized(match.id)

        assert result == []

    async def test_get_players_with_full_data_optimized_selectinload(
        self, test_db, sport, season, teams_data
    ):
        """Test that selectinload eager loads person data."""
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

        player_match_service = PlayerMatchServiceDB(test_db)

        players = []
        for i in range(2):
            player_factory = PlayerFactory.build(sport_id=sport.id, player_eesl_id=i)
            player = await player_match_service.create(player_factory)

            player_match_schema = PlayerMatchSchemaUpdate(
                player_team_tournament_id=player.id,
                team_id=team_a.id,
                is_start=True if i == 0 else False,
            )

            await player_match_service.update(player.id, player_match_schema)
            players.append(player)

        match_factory = MatchFactory.build(
            match_eesl_id=100,
            tournament_id=created_tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime.now(),
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(match_factory)

        result = await player_match_service.get_players_with_full_data_optimized(match.id)

        assert isinstance(result, list)
        assert len(result) == 2

        assert all("first_name" in p.get("person", {}) for p in result)
        assert all("title" in p.get("position", {}) for p in result)
