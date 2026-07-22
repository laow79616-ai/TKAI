"""Local immutable persistent configuration APIs."""

from .errors import ConfigurationError
from .loader import ConfigurationLoader
from .manager import ConfigurationManager
from .models import Configuration
from .resolver import ConfigurationResolver, deep_merge

__all__ = (
    "Configuration",
    "ConfigurationError",
    "ConfigurationLoader",
    "ConfigurationManager",
    "ConfigurationResolver",
    "deep_merge",
)
