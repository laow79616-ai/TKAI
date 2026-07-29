"""Semantic version compatibility and upgrade metadata."""

from tkai.v7.capabilities.contracts import Deprecation, UpgradePath
from tkai.v7.capabilities.framework import compatible
from tkai.v7.contracts import Version, VersionRange

__all__ = (
    "Deprecation",
    "UpgradePath",
    "Version",
    "VersionRange",
    "compatible",
)
