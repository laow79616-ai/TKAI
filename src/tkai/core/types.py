"""
TKAI Core Types

Shared type definitions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, TypeAlias, TypedDict


# ----------------------------------------------------------------------
# Common Aliases
# ----------------------------------------------------------------------

PathLike: TypeAlias = str | Path

JsonDict: TypeAlias = dict[str, Any]

JsonList: TypeAlias = list[Any]


# ----------------------------------------------------------------------
# TypedDict
# ----------------------------------------------------------------------

class ProjectData(TypedDict, total=False):
    name: str
    version: str
    template: str
    author: str
    description: str
    metadata: JsonDict


class WorkspaceData(TypedDict, total=False):
    root: str
    cache: str
    output: str
    temp: str


# ----------------------------------------------------------------------
# Protocols
# ----------------------------------------------------------------------

class Serializable(Protocol):
    """Objects that can be serialized."""

    def to_dict(self) -> JsonDict:
        ...

    @classmethod
    def from_dict(cls, data: JsonDict):
        ...


class Validatable(Protocol):
    """Objects that support validation."""

    def validate(self) -> bool:
        ...