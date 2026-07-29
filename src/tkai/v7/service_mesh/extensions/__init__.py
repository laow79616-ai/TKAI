"""Explicit local service mesh extension contract."""

from __future__ import annotations

from typing import Protocol

from tkai.v7.service_mesh.framework import ServiceRegistry


class ServiceMeshExtension(Protocol):
    def register(self, registry: ServiceRegistry) -> None: ...


__all__ = ("ServiceMeshExtension",)
