import pytest

from src.positions.db_services import PositionServiceDB
from src.positions.schemas import PositionSchemaCreate, PositionSchemaUpdate
from src.sports.db_services import SportServiceDB
from tests.factories import SportFactorySample


@pytest.mark.asyncio
class TestPositionViews:
    async def test_create_position_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        position_data = PositionSchemaCreate(title="Quarterback", sport_id=sport.id)

        response = await client.post("/api/positions/", json=position_data.model_dump())

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_position_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        position_service = PositionServiceDB(test_db)
        position_data = PositionSchemaCreate(title="Quarterback", sport_id=sport.id)
        created = await position_service.create(position_data)

        update_data = PositionSchemaUpdate(title="Updated Position")

        response = await client.put(f"/api/positions/{created.id}/", json=update_data.model_dump())

        assert response.status_code == 200
        assert response.json()["title"] == "Updated Position"

    async def test_update_position_not_found(self, client):
        update_data = PositionSchemaUpdate(title="Updated Position")

        response = await client.put("/api/positions/99999/", json=update_data.model_dump())

        assert response.status_code == 404

    async def test_get_position_by_title_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        position_service = PositionServiceDB(test_db)
        position_data = PositionSchemaCreate(title="Quarterback", sport_id=sport.id)
        created = await position_service.create(position_data)

        response = await client.get("/api/positions/title/Quarterback/")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_all_positions_endpoint(self, client, test_db):
        """Test getting all positions."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        position_service = PositionServiceDB(test_db)
        await position_service.create(PositionSchemaCreate(title="Quarterback", sport_id=sport.id))
        await position_service.create(PositionSchemaCreate(title="Running Back", sport_id=sport.id))

        response = await client.get("/api/positions/")

        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_position_by_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        position_service = PositionServiceDB(test_db)
        position_data = PositionSchemaCreate(title="Quarterback", sport_id=sport.id)
        created = await position_service.create(position_data)

        response = await client.get(f"/api/positions/id/{created.id}")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_position_by_id_not_found(self, client):
        response = await client.get("/api/positions/id/99999")

        assert response.status_code == 404

    async def test_delete_position_endpoint_as_admin(self, client, test_db):
        from src.auth.security import create_access_token, get_password_hash
        from src.core.models import RoleDB, UserDB, UserRoleDB
        from src.users.schemas import UserSchemaCreate

        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        position_service = PositionServiceDB(test_db)
        position_data = PositionSchemaCreate(title="Test Position", sport_id=sport.id)
        position = await position_service.create(position_data)

        async with test_db.async_session() as session:
            role = RoleDB(name="admin", description="Admin role")
            session.add(role)
            await session.flush()
            await session.refresh(role)

            user = UserDB(
                username="test_admin",
                email="admin@test.com",
                hashed_password=get_password_hash("SecurePass123!"),
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)

            session.add(UserRoleDB(user_id=user.id, role_id=role.id))
            await session.commit()
            await session.refresh(user, ["roles"])

        token = create_access_token(data={"sub": str(user.id)})

        response = await client.delete(
            f"/api/positions/id/{position.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    async def test_delete_position_endpoint_unauthorized(self, client):
        response = await client.delete("/api/positions/id/1")

        assert response.status_code == 401

    async def test_get_position_by_title_not_found(self, client):
        response = await client.get("/api/positions/title/NonExistent/")

        assert response.status_code == 404
