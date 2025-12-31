from typing import TYPE_CHECKING, Any, Callable, TypeVar

from src.core.models.base import Database
from src.logging_config import get_logger

logger = get_logger("backend_logger_service_registry")

if TYPE_CHECKING:
    from src.core.models import BaseServiceDB


T = TypeVar("T", bound="BaseServiceDB")


class ServiceRegistry:
    """Registry for managing service instances with dependency injection support."""

    def __init__(self, database: Database):
        self.database = database
        self._services: dict[str, Callable[[], Any]] = {}
        self._singletons: dict[str, Any] = {}
        self._logger = get_logger("backend_logger_service_registry", self)
        self._logger.debug("Initialized ServiceRegistry")

    def register(
        self,
        service_name: str,
        factory: Callable[..., T],
        singleton: bool = False,
    ) -> None:
        """Register a service factory.

        Args:
            service_name: Unique name for the service
            factory: Factory function that creates the service instance
            singleton: If True, the service instance will be cached
        """
        if service_name in self._services:
            self._logger.warning(
                f"Service '{service_name}' already registered, overwriting"
            )
        self._services[service_name] = factory
        self._logger.debug(
            f"Registered service '{service_name}' (singleton={singleton})"
        )

    def get(self, service_name: str) -> T:
        """Get a service instance by name.

        Args:
            service_name: Name of the registered service

        Returns:
            Service instance

        Raises:
            KeyError: If service is not registered
        """
        if service_name not in self._services:
            raise KeyError(f"Service '{service_name}' not registered")

        factory = self._services[service_name]
        return factory(self.database)

    def get_singleton(self, service_name: str) -> T:
        """Get a singleton service instance by name.

        Args:
            service_name: Name of the registered service

        Returns:
            Cached service instance
        """
        if service_name not in self._services:
            raise KeyError(f"Service '{service_name}' not registered")

        if service_name not in self._singletons:
            factory = self._services[service_name]
            self._singletons[service_name] = factory(self.database)
            self._logger.debug(f"Created singleton instance for '{service_name}'")

        return self._singletons[service_name]

    def has(self, service_name: str) -> bool:
        """Check if a service is registered.

        Args:
            service_name: Name of the service

        Returns:
            True if service is registered, False otherwise
        """
        return service_name in self._services

    def clear_singletons(self) -> None:
        """Clear all cached singleton instances."""
        self._singletons.clear()
        self._logger.debug("Cleared all singleton instances")


_global_registry: ServiceRegistry | None = None


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance.

    Returns:
        Global ServiceRegistry instance

    Raises:
        RuntimeError: If registry is not initialized
    """
    global _global_registry
    if _global_registry is None:
        raise RuntimeError(
            "ServiceRegistry not initialized. Call init_service_registry() first."
        )
    return _global_registry


def init_service_registry(database: Database) -> ServiceRegistry:
    """Initialize the global service registry.

    Args:
        database: Database instance for service initialization

    Returns:
        Initialized ServiceRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ServiceRegistry(database)
        logger.info("Global ServiceRegistry initialized")
    return _global_registry


def register_service(
    service_name: str,
    factory: Callable[..., T],
    singleton: bool = False,
) -> None:
    """Register a service with the global registry.

    Args:
        service_name: Unique name for the service
        factory: Factory function that creates the service instance
        singleton: If True, the service instance will be cached
    """
    registry = get_service_registry()
    registry.register(service_name, factory, singleton)


def get_service(service_name: str) -> T:
    """Get a service instance from the global registry.

    Args:
        service_name: Name of the registered service

    Returns:
        Service instance
    """
    registry = get_service_registry()
    return registry.get(service_name)


def get_service_singleton(service_name: str) -> T:
    """Get a singleton service instance from the global registry.

    Args:
        service_name: Name of the registered service

    Returns:
        Cached service instance
    """
    registry = get_service_registry()
    return registry.get_singleton(service_name)
