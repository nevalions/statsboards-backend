import pytest

from src.global_settings.schemas import GlobalSettingSchemaUpdate


@pytest.mark.asyncio
class TestGlobalSettingViews:
    async def test_create_setting_endpoint(self, client):
        setting_data = {
            "key": "test.create.key",
            "value": "test_value",
            "value_type": "string",
            "category": "test",
            "description": "Test setting",
        }

        response = await client.post("/api/settings/", json=setting_data)

        assert response.status_code == 200
        assert response.json()["id"] > 0
        assert response.json()["key"] == "test.create.key"

    async def test_create_setting_unauthorized(self, client):
        setting_data = {
            "key": "test.unauthorized.key",
            "value": "test_value",
            "value_type": "string",
            "category": "test",
            "description": "Test setting",
        }

        response = await client.post("/api/settings/", json=setting_data)

        assert response.status_code == 401

    async def test_update_setting_endpoint(self, client, test_db):
        from src.global_settings.db_services import GlobalSettingServiceDB
        from src.global_settings.schemas import GlobalSettingSchemaCreate

        service = GlobalSettingServiceDB(test_db)
        setting_data = GlobalSettingSchemaCreate(
            key="test.update.key",
            value="original_value",
            value_type="string",
            category="test",
        )
        created = await service.create(setting_data)

        update_data = GlobalSettingSchemaUpdate(value="updated_value")

        response = await client.put(
            f"/api/settings/{created.id}/",
            json=update_data.model_dump(),
        )

        assert response.status_code == 200

    async def test_update_setting_unauthorized(self, client):
        update_data = GlobalSettingSchemaUpdate(value="updated_value")

        response = await client.put("/api/settings/1/", json=update_data.model_dump())

        assert response.status_code == 401

    async def test_get_all_settings_endpoint(self, client, test_db):
        from src.global_settings.db_services import GlobalSettingServiceDB
        from src.global_settings.schemas import GlobalSettingSchemaCreate

        service = GlobalSettingServiceDB(test_db)
        await service.create(
            GlobalSettingSchemaCreate(
                key="test.1",
                value="value1",
                value_type="string",
                category="test",
            )
        )
        await service.create(
            GlobalSettingSchemaCreate(
                key="test.2",
                value="value2",
                value_type="string",
                category="test",
            )
        )

        response = await client.get("/api/settings/")

        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_setting_by_id_endpoint(self, client, test_db):
        from src.global_settings.db_services import GlobalSettingServiceDB
        from src.global_settings.schemas import GlobalSettingSchemaCreate

        service = GlobalSettingServiceDB(test_db)
        setting = await service.create(
            GlobalSettingSchemaCreate(
                key="test.byid.key",
                value="value",
                value_type="string",
                category="test",
            )
        )

        response = await client.get(f"/api/settings/id/{setting.id}/")

        assert response.status_code == 200
        assert response.json()["content"]["id"] == setting.id

    async def test_get_setting_value_endpoint(self, client, test_db):
        from src.global_settings.db_services import GlobalSettingServiceDB
        from src.global_settings.schemas import GlobalSettingSchemaCreate

        service = GlobalSettingServiceDB(test_db)
        setting = await service.create(
            GlobalSettingSchemaCreate(
                key="test.getvalue.key",
                value="test_value",
                value_type="string",
                category="test",
            )
        )

        response = await client.get(f"/api/settings/value/{setting.key}/")

        assert response.status_code == 200
        assert response.json()["value"] == "test_value"

    async def test_get_setting_value_not_found(self, client):
        response = await client.get("/api/settings/value/nonexistent.key/")

        assert response.status_code == 404

    async def test_get_settings_by_category_endpoint(self, client, test_db):
        from src.global_settings.db_services import GlobalSettingServiceDB
        from src.global_settings.schemas import GlobalSettingSchemaCreate

        service = GlobalSettingServiceDB(test_db)
        await service.create(
            GlobalSettingSchemaCreate(
                key="test.cat1.key",
                value="value1",
                value_type="string",
                category="test_category",
            )
        )
        await service.create(
            GlobalSettingSchemaCreate(
                key="test.cat2.key",
                value="value2",
                value_type="string",
                category="test_category",
            )
        )

        response = await client.get("/api/settings/category/test_category/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_get_settings_grouped_endpoint(self, client, test_db):
        from src.global_settings.db_services import GlobalSettingServiceDB
        from src.global_settings.schemas import GlobalSettingSchemaCreate

        service = GlobalSettingServiceDB(test_db)
        await service.create(
            GlobalSettingSchemaCreate(
                key="test.grouped1.key",
                value="value1",
                value_type="string",
                category="category1",
            )
        )
        await service.create(
            GlobalSettingSchemaCreate(
                key="test.grouped2.key",
                value="value2",
                value_type="string",
                category="category2",
            )
        )

        response = await client.get("/api/settings/grouped/")

        assert response.status_code == 200
        assert "category1" in response.json()
        assert "category2" in response.json()

    async def test_delete_setting_endpoint(self, client, test_db):
        from src.global_settings.db_services import GlobalSettingServiceDB
        from src.global_settings.schemas import GlobalSettingSchemaCreate

        service = GlobalSettingServiceDB(test_db)
        setting = await service.create(
            GlobalSettingSchemaCreate(
                key="test.delete.key",
                value="value",
                value_type="string",
                category="test",
            )
        )

        response = await client.delete(f"/api/settings/id/{setting.id}")

        assert response.status_code == 200

    async def test_delete_setting_unauthorized(self, client):
        response = await client.delete("/api/settings/id/1")

        assert response.status_code == 401
