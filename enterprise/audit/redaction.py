"""Deterministic bounded audit redaction; not a DLP or compliance system."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .models import AuditEvent

_SENSITIVE = frozenset(
    {
        "password",
        "secret",
        "token",
        "authorization",
        "api_key",
        "credential",
        "private_key",
        "cookie",
    }
)


@dataclass(frozen=True, slots=True)
class AuditRedactionRule:
    field: str
    mode: str = "mask"


@dataclass(frozen=True, slots=True)
class AuditRedactionPolicy:
    rules: tuple[AuditRedactionRule, ...] = ()
    allowlist: frozenset[str] = field(default_factory=frozenset)
    denylist: frozenset[str] = field(default_factory=lambda: _SENSITIVE)
    truncate_at: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))
        object.__setattr__(
            self, "allowlist", frozenset(item.lower() for item in self.allowlist)
        )
        object.__setattr__(
            self, "denylist", frozenset(item.lower() for item in self.denylist)
        )


@dataclass(frozen=True, slots=True)
class RedactionResult:
    data: Mapping[str, object]
    redacted_fields: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", MappingProxyType(dict(self.data)))


class AuditRedactor:
    """Applies declared remove/mask/truncate rules without mutating an event."""

    def redact(
        self, event: AuditEvent, policy: AuditRedactionPolicy
    ) -> RedactionResult:
        """Return deterministic redacted data using a bounded recursive traversal."""
        rules = {rule.field.lower(): rule.mode for rule in policy.rules}
        redacted: list[str] = []

        def visit(value: object, path: str, depth: int = 0) -> object:
            if depth > 8:
                return "[truncated-depth]"
            if isinstance(value, Mapping):
                result: dict[str, object] = {}
                for key in sorted(value):
                    key_name = str(key)
                    lowered = key_name.lower()
                    mode = rules.get(lowered)
                    sensitive = (
                        lowered in policy.denylist and lowered not in policy.allowlist
                    )
                    if mode == "remove" or sensitive and mode != "mask-allow":
                        redacted.append(f"{path}.{key_name}" if path else key_name)
                        continue
                    child = visit(
                        value[key],
                        f"{path}.{key_name}" if path else key_name,
                        depth + 1,
                    )
                    if mode == "mask":
                        child = "***"
                        redacted.append(f"{path}.{key_name}" if path else key_name)
                    result[key_name] = child
                return result
            if isinstance(value, tuple) or isinstance(value, list):
                return [visit(item, path, depth + 1) for item in value]
            if isinstance(value, str) and policy.truncate_at is not None:
                return value[: policy.truncate_at]
            return value

        data = visit(event.to_dict(), "")
        assert isinstance(data, dict)
        return RedactionResult(data, tuple(redacted))
