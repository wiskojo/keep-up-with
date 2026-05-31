from __future__ import annotations

from importlib import import_module
from pkgutil import iter_modules

from keep_up_with.core.config import KeepUpWithConfig
from keep_up_with.integrations.base import (
    DataIntegration,
    MessagingClient,
    MessagingContext,
    MessagingIntegration,
)


class IntegrationRegistry:
    def __init__(self) -> None:
        self._data: dict[str, DataIntegration] = {}
        self._messaging: dict[str, MessagingIntegration] = {}

    def data(self, integration: DataIntegration) -> None:
        if integration.name in self._data:
            raise ValueError(f"duplicate data integration: {integration.name}")
        self._data[integration.name] = integration

    def messaging(self, integration: MessagingIntegration) -> None:
        if integration.name in self._messaging:
            raise ValueError(f"duplicate messaging integration: {integration.name}")
        self._messaging[integration.name] = integration

    def data_values(self) -> tuple[DataIntegration, ...]:
        return tuple(self._data.values())

    def messaging_value(self, name: str) -> MessagingIntegration:
        try:
            return self._messaging[name]
        except KeyError as error:
            raise ValueError(f"unknown messaging integration: {name}") from error

    def messaging_values(self) -> tuple[MessagingIntegration, ...]:
        return tuple(self._messaging.values())


def build_registry() -> IntegrationRegistry:
    registry = IntegrationRegistry()
    load_namespace(registry, "keep_up_with.integrations.data")
    load_namespace(registry, "keep_up_with.integrations.messaging")
    return registry


def load_namespace(registry: IntegrationRegistry, package_name: str) -> None:
    package = import_module(package_name)
    for module in iter_modules(package.__path__, f"{package_name}."):
        if not module.ispkg:
            continue
        loaded = import_module(module.name)
        register = getattr(loaded, "register", None)
        if callable(register):
            register(registry)


REGISTRY = build_registry()


def available_data_integrations() -> tuple[DataIntegration, ...]:
    return REGISTRY.data_values()


def available_messaging_integrations() -> tuple[MessagingIntegration, ...]:
    return REGISTRY.messaging_values()


def data_integrations(config: KeepUpWithConfig) -> list[DataIntegration]:
    return [
        integration
        for integration in REGISTRY.data_values()
        if config.integration_enabled(integration.name)
        and not missing_env(config, integration)
    ]


def messaging_integration(config: KeepUpWithConfig) -> MessagingIntegration:
    integration = configured_messaging_integration(config)
    missing = missing_env(config, integration)
    if missing:
        raise ValueError(
            "messaging integration "
            f"{integration.name} missing environment values: {', '.join(missing)}"
        )
    missing_settings = [
        name
        for name in integration.required_settings
        if not config.messaging().model_dump(mode="json").get(name)
    ]
    if missing_settings:
        raise ValueError(
            "messaging integration "
            f"{integration.name} missing settings: {', '.join(missing_settings)}"
        )
    return integration


def configured_messaging_integration(config: KeepUpWithConfig) -> MessagingIntegration:
    return REGISTRY.messaging_value(config.messaging().integration)


def messaging_client(config: KeepUpWithConfig) -> MessagingClient:
    integration = messaging_integration(config)
    return integration.client(
        MessagingContext(
            config=config,
            integration=integration.name,
            settings=config.messaging().model_dump(),
        )
    )


def missing_env(
    config: KeepUpWithConfig,
    integration: DataIntegration | MessagingIntegration,
) -> tuple[str, ...]:
    return tuple(name for name in integration.required_env if not config.has_env(name))
