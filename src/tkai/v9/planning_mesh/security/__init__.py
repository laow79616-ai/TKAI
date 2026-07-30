"""Security helpers for tenant/workspace/planning-isolated metadata."""

from collections.abc import Mapping

from tkai.v9.planning_mesh.contracts import PlanningScope, safe_metadata

RBAC_ACTIONS = frozenset({"read", "review"})


def authorize(action: str, actual: PlanningScope, requested: PlanningScope) -> bool:
    return (
        action in RBAC_ACTIONS
        and actual.tenant == requested.tenant
        and actual.workspace == requested.workspace
        and requested.planning in {"*", actual.planning}
    )


def secure_metadata(values: Mapping[str, object]) -> Mapping[str, object]:
    return safe_metadata(values)


__all__ = ("RBAC_ACTIONS", "authorize", "secure_metadata")
