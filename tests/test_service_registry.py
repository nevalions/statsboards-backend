"""Test service registry module."""

import pytest

from src.core.service_registry import (
    ServiceRegistry,
    get_service_registry,
    init_service_registry,
    register_service,
    get_service,
    get_service_singleton,
)


class SampleService:
    """Sample service for testing."""

    def __init__(self, database, name="test_service"):
        self.database = database
        self.name = name


class AnotherSampleService:
    """Another sample service for testing."""

    def __init__(self, database):
        self.database = database


class TestServiceRegistry:
    """Test ServiceRegistry class."""

    def test_init(self, test_db):
        """Test registry initialization."""
        registry = ServiceRegistry(test_db)

        assert registry.database is test_db
        assert registry._services == {}
        assert registry._singletons == {}

    def test_register_service(self, test_db):
        """Test registering a service."""
        registry = ServiceRegistry(test_db)

        registry.register("test_service", SampleService, singleton=False)

        assert "test_service" in registry._services

    def test_register_singleton_service(self, test_db):
        """Test registering a singleton service."""
        registry = ServiceRegistry(test_db)

        registry.register("singleton_service", SampleService, singleton=True)

        assert "singleton_service" in registry._services
        assert "singleton_service" not in registry._singletons

    def test_register_overwrites_existing(self, test_db):
        """Test that registering same service twice overwrites."""
        registry = ServiceRegistry(test_db)

        registry.register("test_service", SampleService)
        registry.register("test_service", AnotherSampleService)

        assert len([k for k in registry._services.keys() if k == "test_service"]) == 1

    def test_get_service(self, test_db):
        """Test getting a non-singleton service."""
        registry = ServiceRegistry(test_db)
        registry.register("test_service", SampleService, singleton=False)

        service = registry.get("test_service")

        assert isinstance(service, SampleService)
        assert service.database is test_db

    def test_get_singleton_service(self, test_db):
        """Test getting a singleton service."""
        registry = ServiceRegistry(test_db)
        registry.register("singleton_service", SampleService, singleton=True)

        service1 = registry.get_singleton("singleton_service")
        service2 = registry.get_singleton("singleton_service")

        assert service1 is service2
        assert "singleton_service" in registry._singletons

    def test_has_service(self, test_db):
        """Test checking if service is registered."""
        registry = ServiceRegistry(test_db)
        registry.register("test_service", SampleService)

        assert registry.has("test_service") is True
        assert registry.has("nonexistent") is False

    def test_clear_singletons(self, test_db):
        """Test clearing singleton cache."""
        registry = ServiceRegistry(test_db)
        registry.register("singleton_service", SampleService, singleton=True)

        registry.get_singleton("singleton_service")
        assert "singleton_service" in registry._singletons

        registry.clear_singletons()

        assert registry._singletons == {}

    def test_update_database(self, test_db):
        """Test updating database instance."""
        registry = ServiceRegistry(test_db)
        registry.register("singleton_service", SampleService, singleton=True)

        registry.get_singleton("singleton_service")
        assert "singleton_service" in registry._singletons

        from src.core.models.base import Database

        new_db = Database("sqlite+aiosqlite:///:memory:", echo=False)

        registry.update_database(new_db)

        assert registry.database is new_db
        assert registry._singletons == {}

    def test_get_nonexistent_service(self, test_db):
        """Test getting nonexistent service raises KeyError."""
        registry = ServiceRegistry(test_db)

        with pytest.raises(KeyError) as exc_info:
            registry.get("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_get_singleton_nonexistent_service(self, test_db):
        """Test getting nonexistent singleton service raises KeyError."""
        registry = ServiceRegistry(test_db)

        with pytest.raises(KeyError) as exc_info:
            registry.get_singleton("nonexistent")

        assert "nonexistent" in str(exc_info.value)


class TestGlobalRegistryFunctions:
    """Test global service registry functions."""

    def test_init_service_registry(self, test_db):
        """Test initializing global registry."""
        from src.core.service_registry import _global_registry

        global_registry = init_service_registry(test_db)

        assert isinstance(global_registry, ServiceRegistry)
        assert global_registry.database is test_db
        assert global_registry is _global_registry

    def test_register_service_globally(self, test_db):
        """Test registering service globally."""
        init_service_registry(test_db)

        register_service("global_test_service", SampleService)

        registry = get_service_registry()
        assert registry.has("global_test_service") is True

    def test_get_service_globally(self, test_db):
        """Test getting service globally."""
        init_service_registry(test_db)
        register_service("global_test_service", SampleService)

        service = get_service("global_test_service")

        assert isinstance(service, SampleService)

    def test_get_service_singleton_globally(self, test_db):
        """Test getting singleton service globally."""
        init_service_registry(test_db)
        register_service("global_singleton_service", SampleService, singleton=True)

        service1 = get_service_singleton("global_singleton_service")
        service2 = get_service_singleton("global_singleton_service")

        assert service1 is service2

    def test_reinit_updates_database(self, test_db):
        """Test reinitializing registry updates database."""
        from src.core.models.base import Database

        init_service_registry(test_db)
        first_registry = get_service_registry()

        new_db = Database("sqlite+aiosqlite:///:memory:", echo=False)
        second_registry = init_service_registry(new_db)

        assert second_registry.database is new_db
        assert second_registry is first_registry
        assert second_registry._singletons == {}
