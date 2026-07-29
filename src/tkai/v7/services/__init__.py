"""Dependency injection container and service discovery."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any, cast

from tkai.v7.contracts import ServiceDescriptor, ServiceFactory


class ServiceNotFoundError(LookupError):
    """Raised when a requested service is unavailable."""


@dataclass
class _Registration:
    descriptor: ServiceDescriptor
    factory: ServiceFactory
    singleton: bool
    instance: object | None = None


class ServiceContainer:
    """Small constructor-independent dependency injection container."""

    def __init__(self) -> None:
        self._registrations: dict[tuple[type[Any], str], _Registration] = {}
        self._lock = RLock()

    def register(
        self,
        descriptor: ServiceDescriptor,
        factory: ServiceFactory,
        *,
        singleton: bool = True,
    ) -> None:
        key = (descriptor.interface, descriptor.name)
        with self._lock:
            if key in self._registrations:
                raise ValueError(f"service {descriptor.name!r} already registered")
            self._registrations[key] = _Registration(descriptor, factory, singleton)

    def register_instance(
        self, descriptor: ServiceDescriptor, instance: object
    ) -> None:
        if not isinstance(instance, descriptor.interface):
            raise TypeError(
                f"service {descriptor.name!r} does not implement "
                f"{descriptor.interface.__name__}"
            )
        self.register(descriptor, lambda _: instance)
        self._registrations[(descriptor.interface, descriptor.name)].instance = instance

    def resolve(self, interface: type[Any], name: str | None = None) -> Any:
        with self._lock:
            matches = [
                registration
                for (
                    registered_interface,
                    registered_name,
                ), registration in self._registrations.items()
                if registered_interface is interface
                and (name is None or registered_name == name)
            ]
            if len(matches) != 1:
                raise ServiceNotFoundError(
                    f"expected one service for {interface.__name__}, "
                    f"found {len(matches)}"
                )
            registration = matches[0]
            if registration.singleton and registration.instance is not None:
                return registration.instance
            instance = registration.factory(self)
            if not isinstance(instance, interface):
                raise TypeError(
                    f"factory {registration.descriptor.name!r} returned an "
                    f"incompatible service"
                )
            if registration.singleton:
                registration.instance = instance
            return cast(Any, instance)

    def discover(self, capability: str | None = None) -> tuple[ServiceDescriptor, ...]:
        with self._lock:
            descriptors = (
                registration.descriptor for registration in self._registrations.values()
            )
            return tuple(
                sorted(
                    (
                        descriptor
                        for descriptor in descriptors
                        if capability is None or capability in descriptor.capabilities
                    ),
                    key=lambda descriptor: (descriptor.name, descriptor.version),
                )
            )


__all__ = ("ServiceContainer", "ServiceNotFoundError")
