"""Reference-only release descriptors with no publication side effects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReleaseChannel(str, Enum):
    DEVELOPMENT = "development"
    CANDIDATE = "candidate"
    GENERAL_AVAILABILITY = "general_availability"


@dataclass(frozen=True, slots=True)
class ReleaseDescriptor:
    release_id: str
    package_id: str
    version: str
    channel: ReleaseChannel = ReleaseChannel.DEVELOPMENT

    def __post_init__(self) -> None:
        if not self.release_id or not self.package_id or not self.version:
            raise ValueError("Release id, package id, and version are required.")


@dataclass(frozen=True, slots=True)
class ReleaseManifest:
    descriptor: ReleaseDescriptor
    notes: str = ""


@dataclass(frozen=True, slots=True)
class ReleasePolicy:
    allow_general_availability: bool = False


@dataclass(frozen=True, slots=True)
class ReleaseSnapshot:
    releases: tuple[ReleaseManifest, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "releases", tuple(self.releases))
