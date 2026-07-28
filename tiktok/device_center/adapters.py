"""Narrow integration ports for existing TikTok and shared services."""
from __future__ import annotations

from typing import Any, Protocol

from .models import Device, DeviceType


class DeviceRuntimePort(Protocol):
    def discover(self) -> list[dict[str, Any]]: ...
    def reconnect(self, device: Device) -> bool: ...
    def restart(self, device: Device) -> bool: ...
    def reinitialize(self, device: Device) -> bool: ...
    def reload_profile(self, device: Device) -> bool: ...


class RiskControlPort(Protocol):
    def has_unresolved_restriction(
        self, tenant: str, workspace: str, account_reference: str
    ) -> bool: ...


class IntegrationPort(Protocol):
    def notify(
        self, event: str, device_reference: str, context: dict[str, str]
    ) -> None: ...


class ReferenceDeviceRuntime:
    """Safe deterministic adapter; never talks to a live device or TikTok."""

    def __init__(self, discovered: list[dict[str, Any]] | None = None) -> None:
        self.discovered = discovered or []

    def discover(self) -> list[dict[str, Any]]:
        return list(self.discovered)

    def reconnect(self, device: Device) -> bool:
        return bool(device.serial_reference)

    def restart(self, device: Device) -> bool:
        return bool(device.serial_reference)

    def reinitialize(self, device: Device) -> bool:
        return device.type is not DeviceType.FUTURE_EXTENSION

    def reload_profile(self, device: Device) -> bool:
        return bool(device.profile_id)


class PermissiveRiskControl:
    def has_unresolved_restriction(
        self, tenant: str, workspace: str, account_reference: str
    ) -> bool:
        del tenant, workspace, account_reference
        return False


class NullIntegrationPort:
    def notify(
        self, event: str, device_reference: str, context: dict[str, str]
    ) -> None:
        del event, device_reference, context
