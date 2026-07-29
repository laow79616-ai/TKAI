"""Stable contracts shared by the TKAI V7 foundation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class LifecycleState(str, Enum):
    """States supported by kernel-managed components."""

    CREATED = "created"
    INITIALIZED = "initialized"
    STARTED = "started"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(frozen=True, order=True)
class Version:
    """A small semantic version value used for contract negotiation."""

    major: int
    minor: int = 0
    patch: int = 0

    @classmethod
    def parse(cls, value: str) -> Version:
        parts = value.strip().lstrip("v").split(".")
        if not 1 <= len(parts) <= 3:
            raise ValueError(f"invalid version: {value!r}")
        try:
            numbers = [int(part) for part in parts]
        except ValueError as error:
            raise ValueError(f"invalid version: {value!r}") from error
        if any(number < 0 for number in numbers):
            raise ValueError(f"invalid version: {value!r}")
        numbers.extend([0] * (3 - len(numbers)))
        return cls(*numbers)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True)
class VersionRange:
    """Inclusive version range for a module or interface."""

    minimum: Version
    maximum: Version

    def supports(self, version: Version) -> bool:
        return self.minimum <= version <= self.maximum


@dataclass(frozen=True)
class Capability:
    """A named, versioned ability exposed by a module or service."""

    name: str
    version: Version = Version(7)
    provider: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ServiceDescriptor:
    """Metadata used for service registration and discovery."""

    name: str
    interface: type[Any]
    version: Version
    capabilities: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ModuleDescriptor:
    """Metadata used by the module registry and extension loader."""

    name: str
    version: Version
    kernel_versions: VersionRange = VersionRange(Version(7), Version(7, 99, 99))
    capabilities: tuple[Capability, ...] = ()


@runtime_checkable
class Lifecycle(Protocol):
    """Lifecycle contract for kernel-managed components."""

    def initialize(self, context: Mapping[str, object]) -> None: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...


@runtime_checkable
class Module(Lifecycle, Protocol):
    """Contract implemented by loadable V7 modules."""

    @property
    def descriptor(self) -> ModuleDescriptor: ...


class ServiceResolver(Protocol):
    """Minimal dependency resolver contract used by service factories."""

    def resolve(self, interface: type[Any], name: str | None = None) -> Any: ...


ServiceFactory = Callable[[ServiceResolver], object]


@runtime_checkable
class Extension(Protocol):
    """Contract exposed by local, explicitly loaded extensions."""

    def register(self, kernel: Any) -> None: ...


__all__ = (
    "Capability",
    "Extension",
    "Lifecycle",
    "LifecycleState",
    "Module",
    "ModuleDescriptor",
    "ServiceDescriptor",
    "ServiceFactory",
    "ServiceResolver",
    "Version",
    "VersionRange",
)
