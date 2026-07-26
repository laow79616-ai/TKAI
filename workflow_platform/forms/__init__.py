"""Schema-backed input forms."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Form:
    id: str
    schema: dict[str, Any]
    defaults: dict[str, Any] = field(default_factory=dict)
    attachments: bool = False

    def validate(self, values: dict[str, Any]) -> dict[str, Any]:
        result = {**self.defaults, **values}
        required = self.schema.get("required", ())
        missing = [name for name in required if name not in result]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        properties = self.schema.get("properties", {})
        for name, value in result.items():
            expected = properties.get(name, {}).get("type")
            valid = {
                "string": isinstance(value, str),
                "number": isinstance(value, (int, float)),
                "boolean": isinstance(value, bool),
            }.get(expected, True)
            if not valid:
                raise ValueError(f"Invalid value for field: {name}")
        return result
