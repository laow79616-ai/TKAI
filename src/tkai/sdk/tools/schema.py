"""Deterministic schema validation for explicit Reference Tool arguments."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .errors import ToolValidationError
from .parameter import ToolParameter


@dataclass(frozen=True, slots=True)
class ToolSchema:
    """A minimal immutable argument schema without JSON-schema dependencies."""

    parameters: tuple[ToolParameter, ...] = ()

    def validate(self, arguments: Mapping[str, object]) -> dict[str, object]:
        """Return copied validated arguments and apply declared defaults."""
        known = {parameter.name: parameter for parameter in self.parameters}
        unknown = sorted(set(arguments) - set(known))
        if unknown:
            raise ToolValidationError(f"Unknown tool arguments: {unknown}")
        validated = dict(arguments)
        for parameter in self.parameters:
            if parameter.name not in validated:
                if parameter.required:
                    raise ToolValidationError(
                        f"Missing required tool argument: {parameter.name}"
                    )
                validated[parameter.name] = parameter.default
        return validated
