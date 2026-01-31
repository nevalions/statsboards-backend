from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import APIRouter, FastAPI

from src.core.router_registry import RouterConfig, RouterRegistry, configure_routers


class TestRouterConfig:
    def test_router_config_creation(self):
        config = RouterConfig(
            module_path="src.test", router_name="api_test_router", enabled=True, priority=10
        )
        assert config.module_path == "src.test"
        assert config.router_name == "api_test_router"
        assert config.enabled is True
        assert config.priority == 10

    def test_router_config_defaults(self):
        config = RouterConfig(module_path="src.test", router_name="api_test_router")
        assert config.enabled is True
        assert config.priority == 100

    def test_router_config_lt_comparison(self):
        config1 = RouterConfig(module_path="src.test1", router_name="api_test_router1", priority=10)
        config2 = RouterConfig(module_path="src.test2", router_name="api_test_router2", priority=20)
        assert config1 < config2

    def test_router_config_lt_same_priority(self):
        config1 = RouterConfig(module_path="src.test1", router_name="api_test_router1", priority=10)
        config2 = RouterConfig(module_path="src.test2", router_name="api_test_router2", priority=10)
        result = config1 < config2
        assert result is False

    def test_router_config_lt_non_comparable(self):
        config = RouterConfig(module_path="src.test", router_name="api_test_router")
        with pytest.raises(TypeError):
            config < "not a config"


class TestRouterRegistry:
    @pytest.fixture
    def registry(self):
        return RouterRegistry(src_path=Path(__file__).parent.parent / "src")

    def test_registry_initialization(self):
        registry = RouterRegistry()
        assert registry._routers == []
        assert registry._loaded_routers == {}
        assert registry.src_path == Path(__file__).parent.parent / "src"

    def test_registry_custom_src_path(self, tmp_path):
        registry = RouterRegistry(src_path=tmp_path)
        assert registry.src_path == tmp_path

    def test_register_router(self, registry):
        registry.register_router(
            module_path="src.test", router_name="api_test_router", enabled=True, priority=50
        )
        assert len(registry._routers) == 1
        config = registry._routers[0]
        assert config.module_path == "src.test"
        assert config.router_name == "api_test_router"
        assert config.enabled is True
        assert config.priority == 50

    def test_register_router_defaults(self, registry):
        registry.register_router(module_path="src.test", router_name="api_test_router")
        config = registry._routers[0]
        assert config.enabled is True
        assert config.priority == 100

    def test_get_router_configs(self, registry):
        registry.register_router(module_path="src.test1", router_name="api_router1")
        registry.register_router(module_path="src.test2", router_name="api_router2")

        configs = registry.get_router_configs()
        assert len(configs) == 2
        assert configs is not registry._routers
        assert configs[0].router_name == "api_router1"
        assert configs[1].router_name == "api_router2"

    def test_load_router_from_cache(self, registry):
        router = APIRouter()
        registry._loaded_routers["api_test_router"] = router

        config = RouterConfig(module_path="src.test", router_name="api_test_router")
        loaded = registry.load_router(config)

        assert loaded is router
        assert len(registry._loaded_routers) == 1

    @patch("importlib.import_module")
    def test_load_router_success(self, mock_import, registry):
        mock_router = APIRouter()
        mock_module = MagicMock()
        mock_module.api_test_router = mock_router
        mock_import.return_value = mock_module

        config = RouterConfig(module_path="src.test", router_name="api_test_router")
        loaded = registry.load_router(config)

        assert loaded is mock_router
        assert "api_test_router" in registry._loaded_routers

    @patch("importlib.import_module")
    def test_load_router_not_api_router(self, mock_import, registry):
        mock_module = MagicMock()
        mock_module.api_test_router = "not a router"
        mock_import.return_value = mock_module

        config = RouterConfig(module_path="src.test", router_name="api_test_router")

        with pytest.raises(TypeError):
            registry.load_router(config)

    @patch("importlib.import_module")
    def test_load_router_import_error(self, mock_import, registry):
        mock_import.side_effect = ImportError("Module not found")

        config = RouterConfig(module_path="src.missing", router_name="api_missing_router")

        with pytest.raises(ImportError):
            registry.load_router(config)

    def test_register_all_with_app(self, registry):
        router1 = APIRouter()
        router2 = APIRouter()

        config1 = RouterConfig(
            module_path="src.test1", router_name="api_router1", enabled=True, priority=10
        )
        config2 = RouterConfig(
            module_path="src.test2", router_name="api_router2", enabled=True, priority=20
        )

        registry._routers = [config1, config2]
        registry._loaded_routers = {"api_router1": router1, "api_router2": router2}

        app = FastAPI()

        with patch.object(app, "include_router") as mock_include:
            registry.register_all(app)

            assert mock_include.call_count == 2

    def test_register_all_skips_disabled(self, registry):
        router = APIRouter()

        config1 = RouterConfig(
            module_path="src.test1", router_name="api_router1", enabled=False, priority=10
        )
        config2 = RouterConfig(
            module_path="src.test2", router_name="api_router2", enabled=True, priority=20
        )

        registry._routers = [config1, config2]
        registry._loaded_routers = {"api_router1": router, "api_router2": router}

        app = FastAPI()

        with patch.object(app, "include_router") as mock_include:
            registry.register_all(app)

            assert mock_include.call_count == 1

    def test_register_all_priority_order(self, registry):
        router1 = APIRouter(prefix="/high")
        router2 = APIRouter(prefix="/low")

        config1 = RouterConfig(
            module_path="src.test1", router_name="api_router1", enabled=True, priority=100
        )
        config2 = RouterConfig(
            module_path="src.test2", router_name="api_router2", enabled=True, priority=10
        )

        registry._routers = [config1, config2]
        registry._loaded_routers = {"api_router1": router1, "api_router2": router2}

        with patch.object(registry, "load_router") as mock_load:

            def side_effect(config):
                return registry._loaded_routers[config.router_name]

            mock_load.side_effect = side_effect

            app = FastAPI()
            included_routers = []

            def capture_include(router):
                included_routers.append(router)

            app.include_router = capture_include  # type: ignore[assignment]

            registry.register_all(app)

            assert included_routers[0] is router2
            assert included_routers[1] is router1

    def test_discover_routers_non_existent_src(self, tmp_path):
        import logging

        registry = RouterRegistry(src_path=tmp_path / "non_existent")

        records: list[logging.LogRecord] = []

        class ListHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        logger = logging.getLogger("router_registry")
        handler = ListHandler()
        logger.addHandler(handler)

        try:
            registry.discover_routers()
        finally:
            logger.removeHandler(handler)

        assert any("not found" in record.getMessage().lower() for record in records)

    def test_discover_routers_no_init_file(self, tmp_path, caplog):
        domain_dir = tmp_path / "src" / "no_init"
        domain_dir.mkdir(parents=True)

        registry = RouterRegistry(src_path=tmp_path / "src")
        registry.discover_routers()

        assert len(registry._routers) == 0


class TestConfigureRouters:
    @pytest.fixture
    def registry(self):
        return RouterRegistry()

    def test_configure_routers_registers_many_routers(self, registry):
        configure_routers(registry)

        configs = registry.get_router_configs()
        assert len(configs) > 20

    def test_configure_routers_sets_priorities(self, registry):
        configure_routers(registry)

        configs = registry.get_router_configs()

        sport_config = next((c for c in configs if c.router_name == "api_sport_router"), None)
        assert sport_config is not None
        assert sport_config.priority == 10

        user_config = next((c for c in configs if c.router_name == "api_user_router"), None)
        assert user_config is not None
        assert user_config.priority == 200

    def test_configure_routers_all_enabled(self, registry):
        configure_routers(registry)

        configs = registry.get_router_configs()
        for config in configs:
            assert config.enabled is True

    def test_configure_routers_sets_correct_module_paths(self, registry):
        configure_routers(registry)

        configs = registry.get_router_configs()

        sport_config = next((c for c in configs if c.router_name == "api_sport_router"), None)
        assert sport_config is not None
        assert sport_config.module_path == "src.sports"
