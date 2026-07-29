"""V7 configuration validation with safe defaults."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

Validator = Callable[[object], bool]


class ConfigurationError(ValueError):
    """Raised when V7 configuration is invalid."""


@dataclass(frozen=True)
class ConfigurationSchema:
    """Simple dependency-free configuration schema."""

    validators: Mapping[str, Validator] = field(default_factory=dict)
    required: frozenset[str] = frozenset()
    allow_unknown: bool = False

    def validate(self, values: Mapping[str, object]) -> dict[str, object]:
        missing = self.required.difference(values)
        if missing:
            raise ConfigurationError(f"missing configuration: {sorted(missing)}")
        unknown = set(values).difference(self.validators)
        if unknown and not self.allow_unknown:
            raise ConfigurationError(f"unknown configuration: {sorted(unknown)}")
        invalid = [
            key
            for key, validator in self.validators.items()
            if key in values and not validator(values[key])
        ]
        if invalid:
            raise ConfigurationError(f"invalid configuration: {sorted(invalid)}")
        return dict(values)


SAFE_DEFAULTS: dict[str, object] = {
    "auto_migrate": False,
    "auto_load_extensions": False,
    "allow_unknown_configuration": False,
    "default_authorization": "deny",
}


__all__ = (
    "ConfigurationError",
    "ConfigurationSchema",
    "SAFE_DEFAULTS",
    "Validator",
)
