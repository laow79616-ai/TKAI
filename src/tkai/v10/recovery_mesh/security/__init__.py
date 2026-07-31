"""RBAC, isolation, filtering, and recovery non-execution guards."""

from collections.abc import Mapping

from tkai.v10.contracts import Scope
from tkai.v10.security import authorize_scope, filter_secrets, validate_safe_metadata

FORBIDDEN_METADATA_KEYS = frozenset(
    """chain_of_thought hidden_reasoning private_scratchpad scratchpad internal_token_trace
token_trace hidden_prompt system_prompt model_weights secret_context""".split()  # noqa: E501
)


def validate_recovery_metadata(metadata: Mapping[str, object]) -> None:
    validate_safe_metadata(metadata)
    keys = {str(key).casefold().replace("-", "_") for key in metadata}
    if keys & FORBIDDEN_METADATA_KEYS:
        raise ValueError("hidden or private reasoning metadata is forbidden")


def authorize_metadata_read(
    requested: Scope, available: Scope, *, role_references: tuple[str, ...] = ()
) -> None:
    authorize_scope(requested, available)
    if not {"reader", "auditor", "recovery-metadata-reader"}.intersection(
        role_references
    ):
        raise PermissionError("RBAC recovery metadata read denied")


__all__ = (
    "FORBIDDEN_METADATA_KEYS",
    "authorize_metadata_read",
    "filter_secrets",
    "validate_recovery_metadata",
)
