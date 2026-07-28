"""Safe workflow variable and expression resolution."""

import re
from collections.abc import Mapping
from typing import Any

EXPRESSION = re.compile(r"^\$\{([a-zA-Z_][\w.]*)\}$")


class Variables:
    def __init__(
        self,
        *,
        inputs: Mapping[str, Any] | None = None,
        environment: Mapping[str, Any] | None = None,
        workflow: Mapping[str, Any] | None = None,
        runtime: Mapping[str, Any] | None = None,
        secrets: Mapping[str, str] | None = None,
    ) -> None:
        self.values = {
            "input": dict(inputs or {}),
            "environment": dict(environment or {}),
            "workflow": dict(workflow or {}),
            "runtime": dict(runtime or {}),
        }
        self.secrets = dict(secrets or {})

    def resolve(self, expression: str) -> Any:
        match = EXPRESSION.match(expression)
        if not match:
            return expression
        parts = match.group(1).split(".")
        if parts[0] == "secret":
            if len(parts) != 2 or parts[1] not in self.secrets:
                raise KeyError("Unknown secret reference.")
            return {"secret_reference": parts[1]}
        value: Any = self.values
        for part in parts:
            if not isinstance(value, Mapping) or part not in value:
                raise KeyError(f"Unknown variable: {match.group(1)}")
            value = value[part]
        return value

    def output(self) -> dict[str, Any]:
        return dict(self.values["runtime"])
