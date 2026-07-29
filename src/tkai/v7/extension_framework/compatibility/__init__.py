"""Compatibility contracts and semantic-version matching."""

from ..contracts import Compatibility, CompatibilityResult
from ..framework import version_satisfies

__all__ = ("Compatibility", "CompatibilityResult", "version_satisfies")
