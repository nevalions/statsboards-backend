import pytest

from src.core.models import PositionDB
from src.sports.db_services import SportServiceDB
from src.sports.schemas import SportSchemaUpdate
from src.teams.db_services import TeamServiceDB
from tests.factories import PositionFactory, SportFactorySample, TeamFactory


@pytest.mark.asyncio
class TestSportViews:
    async def test_create_sport_endpoint(self, client, test_db):
        sport_data = SportFactorySample.build()

        response = await client.post("/api/sports/", json=sport_data.model_dump())

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_sport_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport_data = SportFactorySample.build()
        created = await sport_service.create(sport_data)

        update_data = SportSchemaUpdate(title="Updated Title")

        response = await client.put(
            "/api/sports/",
            params={"item_id": created.id},
            json=update_data.model_dump(),
        )

        assert response.status_code == 200

    async def test_update_sport_not_found(self, client):
        update_data = SportSchemaUpdate(title="Updated Title")

        response = await client.put(
            "/api/sports/", params={"item_id": 99999}, json=update_data.model_dump()
        )

        assert response.status_code == 404

    async def test_get_sport_by_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport_data = SportFactorySample.build()
        created = await sport_service.create(sport_data)

        response = await client.get(f"/api/sports/id/{created.id}/")

        assert response.status_code == 200
        assert response.json()["content"]["id"] == created.id

    async def test_get_sport_by_id_not_found(self, client):
        response = await client.get("/api/sports/id/99999/")

        assert response.status_code == 404

    async def test_get_all_sports_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        await sport_service.create(SportFactorySample.build())
        await sport_service.create(SportFactorySample.build())

        response = await client.get("/api/sports/")

        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_tournaments_by_sport_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        response = await client.get(f"/api/sports/id/{sport.id}/tournaments")

        assert response.status_code == 200

    async def test_get_teams_by_sport_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        response = await client.get(f"/api/sports/id/{sport.id}/teams")

        assert response.status_code == 200

    async def test_get_players_by_sport_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        response = await client.get(f"/api/sports/id/{sport.id}/players")

        assert response.status_code == 200

    async def test_get_positions_by_sport_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        response = await client.get(f"/api/sports/id/{sport.id}/positions")

        assert response.status_code == 200

    async def test_get_positions_by_sport_endpoint_sorted_alphabetically(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        async with test_db.async_session() as session:
            session.add(PositionDB(title="Zebra", sport_id=sport.id))
            session.add(PositionDB(title="Alpha", sport_id=sport.id))
            session.add(PositionDB(title="Bravo", sport_id=sport.id))
            await session.commit()

        positions = await sport_service.get_positions_by_sport(sport.id)
        assert [p.title for p in positions] == ["Alpha", "Bravo", "Zebra"]

    async def test_get_teams_by_sport_paginated_endpoint(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        team_service = TeamServiceDB(test_db)
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Team A"))
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Team B"))
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Team C"))

        result = await team_service.search_teams_by_sport_with_pagination(sport_id=sport.id)

        assert len(result.data) == 3
        assert result.metadata.total_items == 3

    async def test_get_teams_by_sport_paginated_with_search(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        team_service = TeamServiceDB(test_db)
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Team Alpha"))
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Team Beta"))
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Team Gamma"))

        result = await team_service.search_teams_by_sport_with_pagination(
            sport_id=sport.id, search_query="Alpha"
        )

        assert len(result.data) == 1
        assert result.data[0].title == "Team Alpha"

    async def test_get_teams_by_sport_paginated_with_pagination(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        team_service = TeamServiceDB(test_db)
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Team A"))
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Team B"))
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Team C"))

        result = await team_service.search_teams_by_sport_with_pagination(
            sport_id=sport.id, skip=0, limit=2
        )

        assert len(result.data) == 2
        assert result.metadata.page == 1
        assert result.metadata.items_per_page == 2
        assert result.metadata.total_items == 3

    async def test_get_teams_by_sport_paginated_endpoint_http(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        team_service = TeamServiceDB(test_db)
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Team A"))
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Team B"))
        await team_service.create(TeamFactory.build(sport_id=sport.id, title="Team C"))

        response = await client.get(f"/api/sports/id/{sport.id}/teams/paginated")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "metadata" in data
        assert len(data["data"]) == 3
        assert data["metadata"]["total_items"] == 3
