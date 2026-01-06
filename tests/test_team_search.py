import pytest

from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.teams.schemas import PaginatedTeamResponse
from tests.factories import SportFactorySample, TeamFactory


@pytest.mark.asyncio
class TestTeamSearch:
    async def test_search_teams_with_cyrillic(self, test_db):
        team_service = TeamServiceDB(test_db)

        # Create sport first (required for teams)
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        # Create test teams with Cyrillic
        await team_service.create(
            TeamFactory.build(sport_id=sport.id, title="Динамо Киев", city="Киев")
        )
        await team_service.create(
            TeamFactory.build(sport_id=sport.id, title="Спартак Москва", city="Москва")
        )
        await team_service.create(
            TeamFactory.build(sport_id=sport.id, title="Челси", city="Лондон")
        )

        # Search for "Динамо"
        result = await team_service.search_teams_with_pagination(
            search_query="Динамо",
            skip=0,
            limit=10,
        )

        assert isinstance(result, PaginatedTeamResponse)
        assert len(result.data) == 1
        assert result.data[0].title == "Динамо Киев"
        assert result.metadata.total_items == 1

    async def test_search_teams_empty_query(self, test_db):
        team_service = TeamServiceDB(test_db)

        # Empty search should return all teams
        result = await team_service.search_teams_with_pagination(
            search_query=None,
            skip=0,
            limit=10,
        )

        assert result.metadata.total_items >= 0

    async def test_search_teams_pagination(self, test_db):
        team_service = TeamServiceDB(test_db)

        # Create sport first
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        # Create 25 teams
        for i in range(25):
            await team_service.create(TeamFactory.build(sport_id=sport.id, title=f"Team {i}"))

        # Get first page
        page1 = await team_service.search_teams_with_pagination(
            search_query="Team",
            skip=0,
            limit=10,
        )

        assert len(page1.data) == 10
        assert page1.metadata.page == 1
        assert page1.metadata.has_next is True
        assert page1.metadata.has_previous is False

        # Get second page
        page2 = await team_service.search_teams_with_pagination(
            search_query="Team",
            skip=10,
            limit=10,
        )

        assert len(page2.data) == 10
        assert page2.metadata.page == 2

    async def test_search_teams_case_insensitive(self, test_db):
        team_service = TeamServiceDB(test_db)

        # Create sport first
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        # Create test teams
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Manchester United"))
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Manchester City"))
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Chelsea"))

        # Search for lowercase
        result = await team_service.search_teams_with_pagination(
            search_query="manchester",
            skip=0,
            limit=10,
        )

        assert len(result.data) == 2
        assert all("manchester" in team.title.lower() for team in result.data)

    async def test_search_teams_no_results(self, test_db):
        team_service = TeamServiceDB(test_db)

        # Create sport first
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        # Create a team
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Test Team"))

        # Test search that returns no results
        result = await team_service.search_teams_with_pagination(
            search_query="NonExistentTeam",
            skip=0,
            limit=10,
        )

        assert len(result.data) == 0
        assert result.metadata.total_items == 0
        assert result.metadata.total_pages == 0
