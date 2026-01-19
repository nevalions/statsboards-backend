import pytest

from src.global_settings.schemas import GlobalSettingSchemaCreate, GlobalSettingSchemaUpdate


@pytest.fixture(scope="function")
def global_setting_sample():
    return GlobalSettingSchemaCreate(
        key="test.key",
        value="test_value",
        value_type="string",
        category="test",
        description="Test setting",
    )


@pytest.fixture(scope="function")
def global_setting_int_sample():
    return GlobalSettingSchemaCreate(
        key="test.int.key",
        value="42",
        value_type="int",
        category="test",
        description="Test integer setting",
    )


@pytest.fixture(scope="function")
def global_setting_bool_sample():
    return GlobalSettingSchemaCreate(
        key="test.bool.key",
        value="true",
        value_type="bool",
        category="test",
        description="Test boolean setting",
    )


@pytest.fixture(scope="function")
def global_setting_json_sample():
    return GlobalSettingSchemaCreate(
        key="test.json.key",
        value='{"enabled": true, "count": 5}',
        value_type="json",
        category="test",
        description="Test JSON setting",
    )


@pytest.fixture(scope="function")
async def global_setting(test_global_setting_service, global_setting_sample):
    return await test_global_setting_service.create(global_setting_sample)


@pytest.mark.asyncio
class TestGlobalSettingServiceDB:
    async def test_create_global_setting(
        self,
        test_global_setting_service,
        global_setting_sample,
    ):
        created = await test_global_setting_service.create(global_setting_sample)
        assert created.key == global_setting_sample.key
        assert created.value == global_setting_sample.value
        assert created.value_type == global_setting_sample.value_type
        assert created.category == global_setting_sample.category
        assert created.description == global_setting_sample.description

    async def test_get_by_id(
        self,
        test_global_setting_service,
        global_setting,
    ):
        got = await test_global_setting_service.get_by_id(global_setting.id)
        assert got.id == global_setting.id
        assert got.key == global_setting.key

    async def test_get_by_id_not_found(self, test_global_setting_service):
        got = await test_global_setting_service.get_by_id(99999)
        assert got is None

    async def test_update_global_setting(
        self,
        test_global_setting_service,
        global_setting,
    ):
        update_data = GlobalSettingSchemaUpdate(value="updated_value")
        updated = await test_global_setting_service.update(global_setting.id, update_data)
        assert updated.value == "updated_value"

    async def test_get_value_string(self, test_global_setting_service, global_setting):
        value = await test_global_setting_service.get_value(global_setting.key)
        assert value == "test_value"

    async def test_get_value_int(
        self,
        test_global_setting_service,
        global_setting_int_sample,
    ):
        created = await test_global_setting_service.create(global_setting_int_sample)
        value = await test_global_setting_service.get_value(created.key)
        assert value == 42
        assert isinstance(value, int)

    async def test_get_value_bool(
        self,
        test_global_setting_service,
        global_setting_bool_sample,
    ):
        created = await test_global_setting_service.create(global_setting_bool_sample)
        value = await test_global_setting_service.get_value(created.key)
        assert value is True
        assert isinstance(value, bool)

    async def test_get_value_json(
        self,
        test_global_setting_service,
        global_setting_json_sample,
    ):
        created = await test_global_setting_service.create(global_setting_json_sample)
        value = await test_global_setting_service.get_value(created.key)
        assert value == {"enabled": True, "count": 5}
        assert isinstance(value, dict)

    async def test_get_value_not_found(self, test_global_setting_service):
        value = await test_global_setting_service.get_value("nonexistent.key", default="default")
        assert value == "default"

    async def test_get_all_by_category(
        self,
        test_global_setting_service,
        global_setting,
    ):
        settings = await test_global_setting_service.get_all_by_category("test")
        assert len(settings) == 1
        assert settings[0].key == "test.key"

    async def test_get_all_grouped(
        self,
        test_global_setting_service,
        global_setting,
    ):
        grouped = await test_global_setting_service.get_all_grouped()
        assert "test" in grouped
        assert len(grouped["test"]) == 1
        assert grouped["test"][0]["key"] == "test.key"

    async def test_delete_global_setting(
        self,
        test_global_setting_service,
        global_setting,
    ):
        await test_global_setting_service.delete(global_setting.id)
        got = await test_global_setting_service.get_by_id(global_setting.id)
        assert got is None

    async def test_create_season(
        self,
        test_global_setting_service,
    ):
        from src.seasons.schemas import SeasonSchemaCreate

        season_data = SeasonSchemaCreate(
            year=2025,
            description="Test season via settings",
            iscurrent=True,
        )
        created = await test_global_setting_service.create_season(season_data)
        assert created.year == 2025
        assert created.description == "Test season via settings"
        assert created.iscurrent is True

    async def test_update_season(
        self,
        test_global_setting_service,
    ):
        from src.seasons.schemas import SeasonSchemaCreate, SeasonSchemaUpdate

        season_data = SeasonSchemaCreate(
            year=2026,
            description="Original description",
            iscurrent=False,
        )
        created = await test_global_setting_service.create_season(season_data)

        update_data = SeasonSchemaUpdate(
            year=2026,
            description="Updated description",
            iscurrent=True,
        )
        updated = await test_global_setting_service.update_season(created.id, update_data)
        assert updated.year == 2026
        assert updated.description == "Updated description"
        assert updated.iscurrent is True

    async def test_get_season_by_id(
        self,
        test_global_setting_service,
    ):
        from src.seasons.schemas import SeasonSchemaCreate

        season_data = SeasonSchemaCreate(
            year=2027,
            description="Test season",
            iscurrent=False,
        )
        created = await test_global_setting_service.create_season(season_data)

        got = await test_global_setting_service.get_season_by_id(created.id)
        assert got.id == created.id
        assert got.year == 2027
        assert got.description == "Test season"

    async def test_get_season_by_id_not_found(self, test_global_setting_service):
        got = await test_global_setting_service.get_season_by_id(99999)
        assert got is None

    async def test_delete_season(
        self,
        test_global_setting_service,
    ):
        from src.seasons.schemas import SeasonSchemaCreate

        season_data = SeasonSchemaCreate(
            year=2028,
            description="Test season to delete",
            iscurrent=False,
        )
        created = await test_global_setting_service.create_season(season_data)

        await test_global_setting_service.delete_season(created.id)
        got = await test_global_setting_service.get_season_by_id(created.id)
        assert got is None
