"""Security helpers for tenant/workspace/decision-isolated metadata."""

from collections.abc import Mapping

from tkai.v9.decision_mesh.contracts import DecisionScope, safe_metadata

RBAC_ACTIONS = frozenset({"read", "review"})


def authorize(action: str, actual: DecisionScope, requested: DecisionScope) -> bool:
    return (
        action in RBAC_ACTIONS
        and actual.tenant == requested.tenant
        and actual.workspace == requested.workspace
        and requested.decision in {"*", actual.decision}
    )


def secure_metadata(values: Mapping[str, object]) -> Mapping[str, object]:
    return safe_metadata(values)


__all__ = ("RBAC_ACTIONS", "authorize", "secure_metadata")
