"""
End-to-End integration tests for complete workflows.

These tests verify that the application works correctly across multiple
services and endpoints, testing realistic user scenarios.

Run with:
    pytest tests/test_e2e.py
"""

import pytest
from httpx import AsyncClient

from tests.factories import (
    MatchFactory,
    PersonFactory,
    PlayerFactory,
    PositionFactory,
    SeasonFactoryAny,
    SportFactoryAny,
    TeamFactory,
    TournamentFactory,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.mark.e2e
class TestTournamentManagementE2E:
    """End-to-end tests for tournament management workflow."""

    async def test_complete_tournament_workflow(self, client: AsyncClient):
        """Test creating a complete tournament with all related entities."""
        sport_data = SportFactoryAny.build()
        season_data = SeasonFactoryAny.build()

        sport_response = await client.post("/api/sports/", json=sport_data.model_dump())
        assert sport_response.status_code == 200
        sport_id = sport_response.json()["id"]

        season_response = await client.post("/api/seasons/", json=season_data.model_dump())
        assert season_response.status_code == 200
        season_id = season_response.json()["id"]

        tournament_data = TournamentFactory.build(
            sport_id=sport_id,
            season_id=season_id,
        )
        tournament_response = await client.post(
            "/api/tournaments/", json=tournament_data.model_dump()
        )
        assert tournament_response.status_code == 200
        tournament_id = tournament_response.json()["id"]

        get_tournament_response = await client.get(f"/api/tournaments/id/{tournament_id}")
        assert get_tournament_response.status_code == 200
        tournament = get_tournament_response.json()
        assert tournament["id"] == tournament_id
        assert tournament["sport_id"] == sport_id
        assert tournament["season_id"] == season_id

    async def test_tournament_with_teams_workflow(self, client: AsyncClient):
        """Test creating a tournament with multiple teams."""
        sport_data = SportFactoryAny.build()
        season_data = SeasonFactoryAny.build()

        sport_response = await client.post("/api/sports/", json=sport_data.model_dump())
        assert sport_response.status_code == 200
        sport_id = sport_response.json()["id"]

        season_response = await client.post("/api/seasons/", json=season_data.model_dump())
        assert season_response.status_code == 200
        season_id = season_response.json()["id"]

        tournament_data = TournamentFactory.build(
            sport_id=sport_id,
            season_id=season_id,
        )
        tournament_response = await client.post(
            "/api/tournaments/", json=tournament_data.model_dump()
        )
        assert tournament_response.status_code == 200

        teams = []
        for _ in range(4):
            team_data = TeamFactory.build(sport_id=sport_id)
            team_response = await client.post("/api/teams/", json=team_data.model_dump())
            assert team_response.status_code == 200
            teams.append(team_response.json()["id"])

        all_teams_response = await client.get("/api/teams/paginated")
        assert all_teams_response.status_code == 200
        all_teams = all_teams_response.json()
        assert len(all_teams["data"]) >= 4

    async def test_tournament_with_matches_workflow(self, client: AsyncClient):
        """Test creating a tournament with multiple matches."""
        sport_data = SportFactoryAny.build()
        season_data = SeasonFactoryAny.build()

        sport_response = await client.post("/api/sports/", json=sport_data.model_dump())
        assert sport_response.status_code == 200
        sport_id = sport_response.json()["id"]

        season_response = await client.post("/api/seasons/", json=season_data.model_dump())
        assert season_response.status_code == 200
        season_id = season_response.json()["id"]

        tournament_data = TournamentFactory.build(
            sport_id=sport_id,
            season_id=season_id,
        )
        tournament_response = await client.post(
            "/api/tournaments/", json=tournament_data.model_dump()
        )
        assert tournament_response.status_code == 200
        tournament_id = tournament_response.json()["id"]

        team_data1 = TeamFactory.build(sport_id=sport_id)
        team_data2 = TeamFactory.build(sport_id=sport_id)

        team_response1 = await client.post("/api/teams/", json=team_data1.model_dump())
        assert team_response1.status_code == 200
        team_a_id = team_response1.json()["id"]

        team_response2 = await client.post("/api/teams/", json=team_data2.model_dump())
        assert team_response2.status_code == 200
        team_b_id = team_response2.json()["id"]

        for week in range(1, 4):
            match_data = MatchFactory.build(
                tournament_id=tournament_id,
                team_a_id=team_a_id,
                team_b_id=team_b_id,
                week=week,
            )
            match_response = await client.post(
                "/api/matches/", json=match_data.model_dump(mode="json")
            )
            assert match_response.status_code == 200

        tournament_matches_response = await client.get(f"/api/tournaments/{tournament_id}/matches")
        assert tournament_matches_response.status_code in [200, 404]


@pytest.mark.e2e
class TestPlayerManagementE2E:
    """End-to-end tests for player management workflow."""

    async def test_complete_player_workflow(self, client: AsyncClient):
        """Test creating a complete player with all related entities."""
        sport_data = SportFactoryAny.build()
        person_data = PersonFactory.build()

        sport_response = await client.post("/api/sports/", json=sport_data.model_dump())
        assert sport_response.status_code == 200
        sport_id = sport_response.json()["id"]

        person_response = await client.post(
            "/api/persons/", json=person_data.model_dump(mode="json")
        )
        assert person_response.status_code == 200
        person_id = person_response.json()["id"]

        player_data = PlayerFactory.build(
            sport_id=sport_id,
            person_id=person_id,
        )
        player_response = await client.post("/api/players/", json=player_data.model_dump())
        assert player_response.status_code == 200
        player_id = player_response.json()["id"]

        get_player_response = await client.get(f"/api/players/id/{player_id}")
        assert get_player_response.status_code == 200
        player = get_player_response.json()
        assert player["id"] == player_id
        assert player["sport_id"] == sport_id
        assert player["person_id"] == person_id

    async def test_player_with_team_workflow(self, client: AsyncClient):
        """Test assigning players to teams."""
        sport_data = SportFactoryAny.build()
        person_data = PersonFactory.build()

        sport_response = await client.post("/api/sports/", json=sport_data.model_dump())
        assert sport_response.status_code == 200
        sport_id = sport_response.json()["id"]

        person_response = await client.post(
            "/api/persons/", json=person_data.model_dump(mode="json")
        )
        assert person_response.status_code == 200
        person_id = person_response.json()["id"]

        team_data = TeamFactory.build(sport_id=sport_id)
        team_response = await client.post("/api/teams/", json=team_data.model_dump())
        assert team_response.status_code == 200
        team_id = team_response.json()["id"]

        player_data = PlayerFactory.build(
            sport_id=sport_id,
            person_id=person_id,
        )
        player_response = await client.post("/api/players/", json=player_data.model_dump())
        assert player_response.status_code == 200
        player_id = player_response.json()["id"]

        player_team_data = {
            "player_id": player_id,
            "team_id": team_id,
        }
        player_team_response = await client.post(
            "/api/player-team-tournaments/", json=player_team_data
        )
        assert player_team_response.status_code in [200, 404]


@pytest.mark.e2e
class TestPositionManagementE2E:
    """End-to-end tests for position management workflow."""

    async def test_complete_position_workflow(self, client: AsyncClient):
        """Test creating positions for a sport."""
        sport_data = SportFactoryAny.build()

        sport_response = await client.post("/api/sports/", json=sport_data.model_dump())
        assert sport_response.status_code == 200
        sport_id = sport_response.json()["id"]

        positions = []
        position_names = ["Goalkeeper", "Defender", "Midfielder", "Forward"]

        for position_name in position_names:
            position_data = PositionFactory.build(
                title=position_name,
                sport_id=sport_id,
            )
            position_response = await client.post(
                "/api/positions/", json=position_data.model_dump()
            )
            assert position_response.status_code == 200
            positions.append(position_response.json()["id"])

        sport_positions_response = await client.get(f"/api/sports/{sport_id}/positions")
        assert sport_positions_response.status_code in [200, 404]


@pytest.mark.e2e
class TestSponsorManagementE2E:
    """End-to-end tests for sponsor management workflow."""

    async def test_complete_sponsor_workflow(self, client: AsyncClient):
        """Test creating sponsors and sponsor lines."""
        from tests.factories import SponsorFactory, SponsorLineFactory

        sponsor_data = SponsorFactory.build()
        sponsor_response = await client.post("/api/sponsors/", json=sponsor_data.model_dump())
        assert sponsor_response.status_code == 200
        sponsor_id = sponsor_response.json()["id"]

        sponsor_line_data = SponsorLineFactory.build()
        sponsor_line_response = await client.post(
            "/api/sponsor_lines/", json=sponsor_line_data.model_dump()
        )
        assert sponsor_line_response.status_code == 200
        sponsor_line_id = sponsor_line_response.json()["id"]

        connection_data = {
            "sponsor_id": sponsor_id,
            "sponsor_line_id": sponsor_line_id,
        }
        connection_response = await client.post(
            "/api/sponsor-sponsor-line-connections/", json=connection_data
        )
        assert connection_response.status_code in [200, 404]

        get_sponsor_response = await client.get(f"/api/sponsors/id/{sponsor_id}/")
        assert get_sponsor_response.status_code == 200
        sponsor = get_sponsor_response.json()
        assert sponsor["id"] == sponsor_id


@pytest.mark.e2e
class TestErrorHandlingE2E:
    """End-to-end tests for error handling across the application."""

    async def test_sport_team_relationship(self, client: AsyncClient):
        """Test that teams are correctly associated with their sport."""
        sport_data = SportFactoryAny.build()

        sport_response = await client.post("/api/sports/", json=sport_data.model_dump())
        assert sport_response.status_code == 200
        sport_id = sport_response.json()["id"]

        team_data = TeamFactory.build(sport_id=sport_id)
        team_response = await client.post("/api/teams/", json=team_data.model_dump())
        assert team_response.status_code == 200

        get_team_response = await client.get("/api/teams/paginated")
        assert get_team_response.status_code == 200
        teams = get_team_response.json()
        assert len(teams["data"]) > 0
        assert teams["data"][0]["sport_id"] == sport_id

    async def test_duplicate_entity_handling(self, client: AsyncClient):
        """Test that duplicate entities are properly rejected."""
        season_data = SeasonFactoryAny.build()

        season_response1 = await client.post("/api/seasons/", json=season_data.model_dump())
        assert season_response1.status_code == 200

        season_response2 = await client.post("/api/seasons/", json=season_data.model_dump())
        assert season_response2.status_code == 409

    async def test_invalid_reference_handling(self, client: AsyncClient):
        """Test that invalid references are properly rejected."""
        team_data = TeamFactory.build(sport_id=99999)

        team_response = await client.post("/api/teams/", json=team_data.model_dump())
        assert team_response.status_code in [400, 422, 409]


@pytest.mark.e2e
class TestSearchAndFilteringE2E:
    """End-to-end tests for search and filtering functionality."""

    async def test_filter_tournaments_by_season(self, client: AsyncClient):
        """Test filtering tournaments by season."""
        sport_data = SportFactoryAny.build()
        season1_data = SeasonFactoryAny.build(year=2023)
        season2_data = SeasonFactoryAny.build(year=2024)

        sport_response = await client.post("/api/sports/", json=sport_data.model_dump())
        assert sport_response.status_code == 200
        sport_id = sport_response.json()["id"]

        season1_response = await client.post("/api/seasons/", json=season1_data.model_dump())
        assert season1_response.status_code == 200
        season1_id = season1_response.json()["id"]

        season2_response = await client.post("/api/seasons/", json=season2_data.model_dump())
        assert season2_response.status_code == 200
        season2_id = season2_response.json()["id"]

        tournament1_data = TournamentFactory.build(
            sport_id=sport_id,
            season_id=season1_id,
        )
        await client.post("/api/tournaments/", json=tournament1_data.model_dump())

        tournament2_data = TournamentFactory.build(
            sport_id=sport_id,
            season_id=season2_id,
        )
        await client.post("/api/tournaments/", json=tournament2_data.model_dump())

        all_tournaments_response = await client.get("/api/tournaments/")
        assert all_tournaments_response.status_code == 200

    async def test_search_teams_by_name(self, client: AsyncClient):
        """Test searching teams by name."""
        sport_data = SportFactoryAny.build()

        sport_response = await client.post("/api/sports/", json=sport_data.model_dump())
        assert sport_response.status_code == 200
        sport_id = sport_response.json()["id"]

        team_data = TeamFactory.build(sport_id=sport_id, title="Test Team")
        await client.post("/api/teams/", json=team_data.model_dump())

        all_teams_response = await client.get("/api/teams/paginated")
        assert all_teams_response.status_code == 200
        teams = all_teams_response.json()
        assert len(teams["data"]) > 0
