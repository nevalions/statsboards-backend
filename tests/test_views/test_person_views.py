from io import BytesIO

import pytest
from PIL import Image

from src.person.db_services import PersonServiceDB
from src.person.schemas import PersonSchemaUpdate
from src.player.db_services import PlayerServiceDB
from src.sports.db_services import SportServiceDB
from tests.factories import PersonFactory, PlayerFactory, SportFactoryAny


def create_test_image():
    img = Image.new("RGB", (100, 100), color="red")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


@pytest.mark.asyncio
class TestPersonViews:
    async def test_create_person_endpoint(self, client, test_db):
        PersonServiceDB(test_db)
        person_data = PersonFactory.build(person_eesl_id=100)

        response = await client.post("/api/persons/", json=person_data.model_dump(mode="json"))

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_get_person_by_eesl_id_endpoint(self, client, test_db):
        person_service = PersonServiceDB(test_db)
        person_data = PersonFactory.build(person_eesl_id=100)
        created = await person_service.create_or_update_person(person_data)

        response = await client.get("/api/persons/eesl_id/100")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_person_by_eesl_id_not_found(self, client):
        response = await client.get("/api/persons/eesl_id/99999")

        assert response.status_code == 404

    async def test_update_person_endpoint(self, client, test_db):
        person_service = PersonServiceDB(test_db)
        person_data = PersonFactory.build()
        created = await person_service.create_or_update_person(person_data)

        update_data = PersonSchemaUpdate(first_name="Updated Name")

        response = await client.put(f"/api/persons/{created.id}/", json=update_data.model_dump())

        assert response.status_code == 200
        assert response.json()["first_name"] == "Updated Name"

    async def test_get_all_persons_endpoint(self, client, test_db):
        person_service = PersonServiceDB(test_db)
        await person_service.create_or_update_person(PersonFactory.build())
        await person_service.create_or_update_person(PersonFactory.build())

        response = await client.get("/api/persons/")

        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_person_by_id_endpoint(self, client, test_db):
        person_service = PersonServiceDB(test_db)
        person_data = PersonFactory.build()
        created = await person_service.create_or_update_person(person_data)

        response = await client.get(f"/api/persons/id/{created.id}")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_person_by_id_not_found(self, client):
        response = await client.get("/api/persons/id/99999")

        assert response.status_code == 404

    async def test_upload_person_photo_endpoint(self, client):
        file_content = create_test_image()
        files = {"file": ("test_photo.png", BytesIO(file_content), "image/png")}
        response = await client.post("/api/persons/upload_photo", files=files)

        assert response.status_code == 200
        assert "photoUrl" in response.json()
        assert "persons/photos" in response.json()["photoUrl"]

    async def test_upload_person_photo_with_invalid_file(self, client):
        file_content = b"not a valid image"
        files = {"file": ("test_invalid.txt", BytesIO(file_content), "text/plain")}
        response = await client.post("/api/persons/upload_photo", files=files)

        assert response.status_code == 400

    async def test_upload_and_resize_person_photo_endpoint(self, client):
        file_content = create_test_image()
        files = {"file": ("test_photo.png", BytesIO(file_content), "image/png")}
        response = await client.post("/api/persons/upload_resize_photo", files=files)

        assert response.status_code == 200
        response_data = response.json()
        assert "original" in response_data
        assert "icon" in response_data
        assert "webview" in response_data
        assert "persons/photos" in response_data["original"]
        assert "persons/photos" in response_data["icon"]
        assert "persons/photos" in response_data["webview"]

    async def test_upload_and_resize_person_photo_with_invalid_file(self, client):
        file_content = b"not a valid image"
        files = {"file": ("test_invalid.txt", BytesIO(file_content), "text/plain")}
        response = await client.post("/api/persons/upload_resize_photo", files=files)

        assert response.status_code == 400

    async def test_get_all_persons_paginated_endpoint_success(self, client, test_db):
        """Test paginated endpoint returns correct data."""
        person_service = PersonServiceDB(test_db)
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=1001, second_name="Zoe")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=1002, second_name="Smith")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=1003, second_name="Brown")
        )

        response = await client.get(
            "/api/persons/paginated?page=1&items_per_page=2&order_by=second_name"
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "metadata" in data
        assert len(data["data"]) == 2
        second_names = [p["second_name"] for p in data["data"]]
        assert second_names == ["Brown", "Smith"]

    async def test_get_all_persons_paginated_endpoint_invalid_page(self, client):
        """Test paginated endpoint rejects invalid page number."""
        response = await client.get("/api/persons/paginated?page=0")

        assert response.status_code == 422

    async def test_get_all_persons_paginated_endpoint_invalid_items_per_page(self, client):
        """Test paginated endpoint rejects invalid items_per_page."""
        response = await client.get("/api/persons/paginated?items_per_page=101")

        assert response.status_code == 422

    async def test_get_all_persons_paginated_endpoint_default_sorting(self, client, test_db):
        """Test paginated endpoint uses default sort by second_name."""
        person_service = PersonServiceDB(test_db)
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=2001, second_name="Zebra")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=2002, second_name="Apple")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=2003, second_name="Mango")
        )

        response = await client.get("/api/persons/paginated")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        second_names = [p["second_name"] for p in data["data"]]
        assert second_names == ["Apple", "Mango", "Zebra"]

    async def test_get_all_persons_paginated_endpoint_descending_order(self, client, test_db):
        """Test paginated endpoint with descending order."""
        person_service = PersonServiceDB(test_db)
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=3001, second_name="Alpha")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=3002, second_name="Beta")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=3003, second_name="Gamma")
        )

        response = await client.get("/api/persons/paginated?order_by=second_name&ascending=false")

        assert response.status_code == 200
        data = response.json()
        second_names = [p["second_name"] for p in data["data"]]
        assert second_names == sorted(second_names, reverse=True)

    async def test_get_all_persons_paginated_endpoint_multiple_pages(self, client, test_db):
        """Test paginated endpoint across multiple pages."""
        person_service = PersonServiceDB(test_db)
        for i in range(5):
            await person_service.create_or_update_person(
                PersonFactory.build(person_eesl_id=4000 + i, second_name=f"Name{i}")
            )

        page1 = await client.get("/api/persons/paginated?page=1&items_per_page=2")
        page2 = await client.get("/api/persons/paginated?page=2&items_per_page=2")
        page3 = await client.get("/api/persons/paginated?page=3&items_per_page=2")

        assert page1.status_code == 200
        assert len(page1.json()["data"]) == 2
        assert page2.status_code == 200
        assert len(page2.json()["data"]) == 2
        assert page3.status_code == 200
        assert len(page3.json()["data"]) == 1

    async def test_get_persons_count_endpoint(self, client, test_db):
        """Test count endpoint returns correct total."""
        person_service = PersonServiceDB(test_db)
        await person_service.create_or_update_person(PersonFactory.build(person_eesl_id=5001))
        await person_service.create_or_update_person(PersonFactory.build(person_eesl_id=5002))
        await person_service.create_or_update_person(PersonFactory.build(person_eesl_id=5003))

        response = await client.get("/api/persons/count")

        assert response.status_code == 200
        assert response.json() == {"total_items": 3}

    async def test_get_persons_count_endpoint_empty(self, client, test_db):
        """Test count endpoint returns zero when no records."""
        response = await client.get("/api/persons/count")

        assert response.status_code == 200
        assert response.json() == {"total_items": 0}

    async def test_existing_get_all_persons_endpoint_still_works(self, client, test_db):
        """Test that non-paginated endpoint still works (backward compatibility)."""
        person_service = PersonServiceDB(test_db)
        await person_service.create_or_update_person(PersonFactory.build(person_eesl_id=6001))
        await person_service.create_or_update_person(PersonFactory.build(person_eesl_id=6002))

        response = await client.get("/api/persons/")

        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_all_persons_paginated_search_success(self, client, test_db):
        """Test search functionality in paginated endpoint."""
        person_service = PersonServiceDB(test_db)
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=8001, first_name="Alice", second_name="Johnson")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=8002, first_name="Bob", second_name="Smith")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=8003, first_name="Charlie", second_name="Johnson")
        )

        response = await client.get("/api/persons/paginated?search=Johnson")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "metadata" in data
        assert len(data["data"]) == 2
        names = [p["first_name"] for p in data["data"]]
        assert "Alice" in names
        assert "Charlie" in names
        assert "Bob" not in names

    async def test_get_all_persons_paginated_with_metadata(self, client, test_db):
        """Test paginated endpoint returns correct metadata."""
        person_service = PersonServiceDB(test_db)
        for i in range(5):
            await person_service.create_or_update_person(
                PersonFactory.build(
                    person_eesl_id=9000 + i,
                    first_name=f"Person{i}",
                    second_name="Test",
                )
            )

        response = await client.get("/api/persons/paginated?search=Test&page=1&items_per_page=2")

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["page"] == 1
        assert data["metadata"]["items_per_page"] == 2
        assert data["metadata"]["total_items"] == 5
        assert data["metadata"]["total_pages"] == 3
        assert data["metadata"]["has_next"] is True
        assert data["metadata"]["has_previous"] is False
        assert len(data["data"]) == 2

    async def test_get_all_persons_paginated_search_no_results(self, client, test_db):
        """Test search with no matching results returns empty data."""
        person_service = PersonServiceDB(test_db)
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=10001, first_name="Alice", second_name="Smith")
        )

        response = await client.get("/api/persons/paginated?search=XYZNonExistent")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0
        assert data["metadata"]["total_items"] == 0

    async def test_get_all_persons_paginated_search_with_pagination(self, client, test_db):
        """Test search works with pagination."""
        person_service = PersonServiceDB(test_db)
        for i in range(5):
            await person_service.create_or_update_person(
                PersonFactory.build(
                    person_eesl_id=11000 + i,
                    first_name=f"Test{i}",
                    second_name="Searchable",
                )
            )

        page1 = await client.get("/api/persons/paginated?search=Searchable&page=1&items_per_page=2")
        page2 = await client.get("/api/persons/paginated?search=Searchable&page=2&items_per_page=2")

        assert page1.status_code == 200
        assert len(page1.json()["data"]) == 2
        assert page2.status_code == 200
        assert len(page2.json()["data"]) == 2

    async def test_get_all_persons_paginated_empty_search_all_results(self, client, test_db):
        """Test empty search query returns all persons (no filter)."""
        person_service = PersonServiceDB(test_db)
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=12001, first_name="Alice", second_name="Zoe")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=12002, first_name="Bob", second_name="Alpha")
        )

        response = await client.get("/api/persons/paginated?search=")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 2

    async def test_get_persons_not_in_sport_endpoint(self, client, test_db):
        """Test get persons not in sport endpoint returns correct data."""
        person_service = PersonServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)

        sport = await sport_service.create(SportFactoryAny.build())

        person1 = await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=1001, first_name="Alice", second_name="SportPlayer")
        )
        person2 = await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=1002, first_name="Bob", second_name="NoSportPlayer")
        )
        person3 = await person_service.create_or_update_person(
            PersonFactory.build(
                person_eesl_id=1003, first_name="Charlie", second_name="SportPlayer2"
            )
        )

        player1_data = PlayerFactory.build(
            sport_id=sport.id, person_id=person1.id, player_eesl_id=2001
        )
        player2_data = PlayerFactory.build(
            sport_id=sport.id, person_id=person3.id, player_eesl_id=2002
        )

        await player_service.create(player1_data)
        await player_service.create(player2_data)

        response = await client.get(f"/api/persons/not-in-sport/{sport.id}")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "metadata" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["first_name"] == person2.first_name
        assert data["data"][0]["second_name"] == person2.second_name
        assert data["metadata"]["total_items"] == 1

    async def test_get_persons_not_in_sport_with_search(self, client, test_db):
        """Test search parameter works with sport filtering."""
        person_service = PersonServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)

        sport = await sport_service.create(SportFactoryAny.build())

        person1 = await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=2001, first_name="Alice", second_name="SearchTest")
        )
        person2 = await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=2002, first_name="Alice", second_name="NoSport")
        )

        player1_data = PlayerFactory.build(
            sport_id=sport.id, person_id=person1.id, player_eesl_id=3001
        )

        await player_service.create(player1_data)

        response = await client.get(f"/api/persons/not-in-sport/{sport.id}?search=Alice")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["first_name"] == person2.first_name
        assert data["data"][0]["second_name"] == person2.second_name

    async def test_get_all_persons_not_in_sport_endpoint(self, client, test_db):
        """Test get all persons not in sport endpoint without pagination."""
        person_service = PersonServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)

        sport = await sport_service.create(SportFactoryAny.build())

        person1 = await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=3001, first_name="Alice", second_name="SportPlayer")
        )
        person2 = await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=3002, first_name="Bob", second_name="NoSportPlayer")
        )
        person3 = await person_service.create_or_update_person(
            PersonFactory.build(
                person_eesl_id=3003, first_name="Charlie", second_name="SportPlayer2"
            )
        )

        player1_data = PlayerFactory.build(
            sport_id=sport.id, person_id=person1.id, player_eesl_id=4001
        )
        player2_data = PlayerFactory.build(
            sport_id=sport.id, person_id=person3.id, player_eesl_id=4002
        )

        await player_service.create(player1_data)
        await player_service.create(player2_data)

        response = await client.get(f"/api/persons/not-in-sport/{sport.id}/all")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["first_name"] == person2.first_name
        assert data[0]["second_name"] == person2.second_name
