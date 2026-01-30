"""Additional tests for player views endpoints."""

import pytest

from src.person.db_services import PersonServiceDB
from src.player.db_services import PlayerServiceDB
from src.player.schemas import PlayerSchemaCreate, PlayerSchemaUpdate
from src.sports.db_services import SportServiceDB
from tests.factories import PersonFactory, SportFactorySample


@pytest.mark.asyncio
class TestPlayerViewsEndpointsCoverage:
    """Test suite for covering missing player view endpoints."""

    async def test_get_player_by_eesl_id_endpoint(self, client, test_db):
        """Test get player by eesl_id endpoint."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        await player_service.create_or_update_player(
            PlayerSchemaCreate(sport_id=sport.id, person_id=person.id, player_eesl_id=100)
        )

        response = await client.get("/api/players/eesl_id/100")

        assert response.status_code == 200
        data = response.json()
        assert data["player_eesl_id"] == 100
        assert data["person_id"] == person.id
        assert data["sport_id"] == sport.id

    async def test_get_player_by_eesl_id_not_found(self, client):
        """Test get player by eesl_id when not found."""
        response = await client.get("/api/players/eesl_id/99999")

        assert response.status_code == 404

    async def test_person_by_player_id_endpoint(self, client, test_db):
        """Test get person by player id endpoint."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create_or_update_player(
            PlayerSchemaCreate(sport_id=sport.id, person_id=person.id, player_eesl_id=100)
        )

        response = await client.get(f"/api/players/id/{player.id}/person")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == person.id
        assert data["first_name"] == person.first_name
        assert data["second_name"] == person.second_name

    async def test_person_by_player_id_not_found(self, client):
        """Test get person by player id when not found."""
        response = await client.get("/api/players/id/99999/person")

        assert response.status_code == 404

    async def test_remove_person_from_sport_endpoint(self, client, test_db):
        """Test remove person from sport endpoint."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        await player_service.create_or_update_player(
            PlayerSchemaCreate(sport_id=sport.id, person_id=person.id, player_eesl_id=100)
        )

        response = await client.delete(
            f"/api/players/remove-person-from-sport/personid/{person.id}/sportid/{sport.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_update_player_endpoint(self, client, test_db):
        """Test update player endpoint."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create_or_update_player(
            PlayerSchemaCreate(sport_id=sport.id, person_id=person.id, player_eesl_id=100)
        )

        update_data = PlayerSchemaUpdate(isprivate=True)

        response = await client.put(f"/api/players/{player.id}/", json=update_data.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["isprivate"] is True

    async def test_update_player_endpoint_not_found(self, client):
        """Test update player when not found."""
        update_data = PlayerSchemaUpdate(isprivate=True)

        response = await client.put("/api/players/99999/", json=update_data.model_dump())

        assert response.status_code == 404
