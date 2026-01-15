import pytest

from src.person.db_services import PersonServiceDB
from src.player.db_services import PlayerServiceDB
from src.player.schemas import PlayerSchemaCreate, PlayerSchemaUpdate
from src.sports.db_services import SportServiceDB
from tests.factories import PersonFactory, SportFactorySample


@pytest.mark.asyncio
class TestPlayerViews:
    async def test_create_player_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_data = PlayerSchemaCreate(sport_id=sport.id, person_id=person.id, player_eesl_id=100)

        response = await client.post("/api/players/", json=player_data.model_dump())

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_get_player_by_eesl_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=100)
        )

        player_service = PlayerServiceDB(test_db)
        player_data = PlayerSchemaCreate(sport_id=sport.id, person_id=person.id, player_eesl_id=100)
        created = await player_service.create_or_update_player(player_data)

        response = await client.get("/api/players/eesl_id/100")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_player_by_eesl_id_not_found(self, client):
        response = await client.get("/api/players/eesl_id/99999")

        assert response.status_code == 404

    async def test_update_player_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player_data = PlayerSchemaCreate(sport_id=sport.id, person_id=person.id)
        created = await player_service.create_or_update_player(player_data)

        update_data = PlayerSchemaUpdate(player_eesl_id=200)

        response = await client.put(f"/api/players/{created.id}/", json=update_data.model_dump())

        assert response.status_code == 200

    async def test_get_all_players_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person1 = await person_service.create_or_update_person(PersonFactory.build())
        person2 = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        await player_service.create_or_update_player(
            PlayerSchemaCreate(sport_id=sport.id, person_id=person1.id)
        )
        await player_service.create_or_update_player(
            PlayerSchemaCreate(sport_id=sport.id, person_id=person2.id)
        )

        response = await client.get("/api/players/")

        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_player_by_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player_data = PlayerSchemaCreate(sport_id=sport.id, person_id=person.id)
        created = await player_service.create_or_update_player(player_data)

        response = await client.get(f"/api/players/id/{created.id}")

        assert response.status_code == 200

    async def test_get_player_by_id_not_found(self, client):
        response = await client.get("/api/players/id/99999")

        assert response.status_code == 404

    async def test_get_person_by_player_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player_data = PlayerSchemaCreate(sport_id=sport.id, person_id=person.id)
        created = await player_service.create_or_update_player(player_data)

        response = await client.get(f"/api/players/id/{created.id}/person")

        assert response.status_code == 200


@pytest.mark.asyncio
class TestPlayerSportManagement:
    async def test_add_person_to_sport_success(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.add_person_to_sport(
            person_id=person.id,
            sport_id=sport.id,
        )

        assert player.person_id == person.id
        assert player.sport_id == sport.id

    async def test_add_person_to_sport_duplicate_fails(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        await player_service.add_person_to_sport(
            person_id=person.id,
            sport_id=sport.id,
        )

        with pytest.raises(Exception) as exc_info:
            await player_service.add_person_to_sport(
                person_id=person.id,
                sport_id=sport.id,
            )
        assert exc_info.value.status_code == 409

    async def test_remove_person_from_sport_success(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        await player_service.add_person_to_sport(
            person_id=person.id,
            sport_id=sport.id,
        )

        result = await player_service.remove_person_from_sport(
            person_id=person.id,
            sport_id=sport.id,
        )

        assert result is True

    async def test_remove_person_from_sport_not_found(self, client, test_db):
        player_service = PlayerServiceDB(test_db)

        with pytest.raises(Exception) as exc_info:
            await player_service.remove_person_from_sport(
                person_id=999,
                sport_id=999,
            )
        assert exc_info.value.status_code == 404

    async def test_multiple_players_for_same_person_different_sports(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport1 = await sport_service.create(SportFactorySample.build(title="Sport 1"))
        sport2 = await sport_service.create(SportFactorySample.build(title="Sport 2"))

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player1 = await player_service.add_person_to_sport(
            person_id=person.id,
            sport_id=sport1.id,
        )
        player2 = await player_service.add_person_to_sport(
            person_id=person.id,
            sport_id=sport2.id,
        )

        assert player1.id != player2.id
        assert player1.person_id == person.id
        assert player2.person_id == person.id

    async def test_add_person_to_sport_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        response = await client.post(
            "/api/players/add-person-to-sport",
            json={"person_id": person.id, "sport_id": sport.id},
        )

        assert response.status_code == 200
        assert response.json()["person_id"] == person.id
        assert response.json()["sport_id"] == sport.id

    async def test_remove_person_from_sport_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        await player_service.add_person_to_sport(
            person_id=person.id,
            sport_id=sport.id,
        )

        response = await client.delete(
            f"/api/players/remove-person-from-sport/personid/{person.id}/sportid/{sport.id}"
        )

        assert response.status_code == 200
        assert response.json()["success"] is True
