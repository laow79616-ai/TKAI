"""Read-only adapters for TKAI V6 through V11."""

from __future__ import annotations

from importlib import import_module
from typing import Any

SUPPORTED = (6, 7, 8, 9, 10, 11)


class ReadOnlyVersionAdapter:
    def __init__(self, version: int) -> None:
        if version not in SUPPORTED:
            raise ValueError("unsupported historical version")
        self.version = version

    def package(self) -> Any:
        try:
            return import_module(f"tkai.v{self.version}")
        except ModuleNotFoundError:
            if self.version == 6:
                return import_module("tkai")
            raise

    def projection(self) -> dict[str, object]:
        package = self.package()
        return {
            "version": self.version,
            "package_version": (
                "6.0.0"
                if self.version == 6
                else getattr(package, "__version__", f"{self.version}.0.0")
            ),
            "read_only": True,
            "mutation_enabled": False,
            "adapter": "bounded-reference",
        }


def compatibility_matrix() -> tuple[dict[str, object], ...]:
    return tuple(ReadOnlyVersionAdapter(version).projection() for version in SUPPORTED)
