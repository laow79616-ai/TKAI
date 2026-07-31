"""Security invariants for local, safe, read-only V11 metadata."""

from __future__ import annotations

from collections.abc import Mapping

from tkai.v11.contracts import Scope

SECRET_MARKERS = (
    "api_key",
    "authorization",
    "cookie",
    "credential",
    "password",
    "secret",
    "session",
    "token",
)
FORBIDDEN_CAPABILITIES = (
    "browser_control",
    "deployment_execution",
    "runtime_mutation",
    "scheduler_mutation",
    "service_control",
    "storage_mutation",
    "tiktok_action",
)


def filter_secrets(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): (
                "[REDACTED]"
                if any(marker in str(key).lower() for marker in SECRET_MARKERS)
                else filter_secrets(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [filter_secrets(item) for item in value]
    return value


def validate_safe_metadata(metadata: Mapping[str, object]) -> None:
    for key, value in metadata.items():
        if any(marker in str(key).lower() for marker in SECRET_MARKERS):
            raise ValueError(f"secret-bearing metadata is forbidden: {key}")
        if isinstance(value, Mapping):
            validate_safe_metadata(value)


def authorize_scope(requested: Scope, available: Scope) -> None:
    for field_name in ("tenant", "workspace", "namespace"):
        if getattr(requested, field_name) != getattr(available, field_name):
            raise PermissionError(f"{field_name} isolation")


def security_projection() -> dict[str, object]:
    return {
        "local_first": True,
        "rbac_compatible": True,
        "tenant_isolation": True,
        "workspace_isolation": True,
        "secret_filtering": True,
        "safe_metadata": True,
        "hidden_reasoning_exposed": False,
        **{capability: False for capability in FORBIDDEN_CAPABILITIES},
    }


__all__ = (
    "FORBIDDEN_CAPABILITIES",
    "SECRET_MARKERS",
    "authorize_scope",
    "filter_secrets",
    "security_projection",
    "validate_safe_metadata",
)
