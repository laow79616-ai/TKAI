"""Explicit Marketplace and Platform boundary contracts without transports."""

from __future__ import annotations

from typing import Protocol

from .models import PackageDescriptor, PackageKind


class MarketplaceAPI(Protocol):
    """Future transport-neutral catalog API; no REST or network client exists."""

    def packages(
        self, kind: PackageKind | None = None
    ) -> tuple[PackageDescriptor, ...]: ...
    def package(self, package_id: str) -> PackageDescriptor: ...


class PackageInstaller(Protocol):
    """Future explicit installer boundary; this architecture never installs packages."""

    def install(self, package: PackageDescriptor) -> None: ...


class SignatureVerifier(Protocol):
    """Future signature boundary; no signing or key management is implemented."""

    def verify(self, package: PackageDescriptor, signature: str) -> bool: ...


class PlatformGateway(Protocol):
    """Future explicit Platform adapter boundary for Marketplace capabilities."""

    def capabilities(self) -> frozenset[str]: ...
