"""Static manifest loading without imports, callbacks, or code execution."""

from __future__ import annotations

from collections.abc import Iterable

from ..contracts import ExtensionManifest


def load_static(
    manifests: Iterable[ExtensionManifest],
) -> tuple[ExtensionManifest, ...]:
    return tuple(manifests)


__all__ = ("load_static",)
