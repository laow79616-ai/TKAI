"""Safe, explicit loading of local V7 extensions."""

from __future__ import annotations

from importlib import import_module
from importlib.metadata import EntryPoint, entry_points
from typing import Any

from tkai.v7.contracts import Extension


class ExtensionLoadError(RuntimeError):
    """Raised when an extension does not satisfy the V7 contract."""


class ExtensionLoader:
    """Loads opt-in extensions; discovery never activates them automatically."""

    ENTRY_POINT_GROUP = "tkai.v7.extensions"

    def discover(self) -> tuple[EntryPoint, ...]:
        return tuple(entry_points().select(group=self.ENTRY_POINT_GROUP))

    def load_entry_point(self, entry_point: EntryPoint) -> Extension:
        return self._validate(entry_point.load())

    def load_path(self, dotted_path: str) -> Extension:
        module_name, separator, attribute = dotted_path.partition(":")
        if not separator or not module_name or not attribute:
            raise ExtensionLoadError("extension path must be 'module:attribute'")
        value: Any = getattr(import_module(module_name), attribute)
        return self._validate(value)

    @staticmethod
    def _validate(value: Any) -> Extension:
        extension = value() if isinstance(value, type) else value
        if not isinstance(extension, Extension):
            raise ExtensionLoadError("extension does not implement register(kernel)")
        return extension


__all__ = ("ExtensionLoadError", "ExtensionLoader")
