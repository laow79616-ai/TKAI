"""Typed interfaces for metadata-only discovery."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from ..contracts import ExtensionManifest


class StaticExtensionProvider(Protocol):
    def manifests(self) -> Iterable[ExtensionManifest]: ...


__all__ = ("StaticExtensionProvider",)
