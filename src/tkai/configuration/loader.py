"""Configuration-source protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class ConfigurationLoader(ABC):
    """Read a local configuration mapping without side effects."""

    @abstractmethod
    def load(self) -> Mapping[str, Any]: ...
    @abstractmethod
    def identifier(self) -> str: ...
