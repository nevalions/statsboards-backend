import pytest
from io import BytesIO
from PIL import Image
from src.person.db_services import PersonServiceDB
from src.person.schemas import PersonSchemaCreate, PersonSchemaUpdate
from tests.factories import PersonFactory
from src.logging_config import setup_logging

setup_logging()


def create_test_image():
    img = Image.new('RGB', (100, 100), color='red')
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()


@pytest.mark.asyncio
class TestPersonViews:
    async def test_create_person_endpoint(self, client, test_db):
        person_service = PersonServiceDB(test_db)
        person_data = PersonFactory.build(person_eesl_id=100)
        
        response = await client.post("/api/persons/", json=person_data.model_dump(mode='json'))
        
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
