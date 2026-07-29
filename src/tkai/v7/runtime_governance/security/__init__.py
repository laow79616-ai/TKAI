"""Scope isolation and secret-filtering boundary."""
from ..contracts import Scope, safe_metadata
from ..framework import IsolationError

__all__ = ("IsolationError", "Scope", "safe_metadata")
