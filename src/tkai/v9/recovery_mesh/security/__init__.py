"""Security boundary and scope authorization."""

from collections.abc import Mapping

from tkai.v9.recovery_mesh.contracts import RecoveryScope, safe_metadata


def authorize(action: str, actual: RecoveryScope, requested: RecoveryScope) -> bool:
    return (
        action in {"read", "review", "approve_reference"}
        and actual.tenant == requested.tenant
        and actual.workspace == requested.workspace
        and actual.namespace == requested.namespace
        and requested.profile in {"*", actual.profile}
    )


def secure_metadata(values: Mapping[str, object]) -> Mapping[str, object]:
    return safe_metadata(values)


__all__ = ("authorize", "secure_metadata")
