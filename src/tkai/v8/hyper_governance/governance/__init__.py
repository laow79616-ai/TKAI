"""Policy aggregation and non-authorizing governance semantics."""

from __future__ import annotations

from collections.abc import Mapping

from tkai.v8.hyper_governance.contracts import GovernanceReference


def normalize_reference(
    value: GovernanceReference | Mapping[str, object], generation: str
) -> GovernanceReference:
    """Normalize external metadata without importing or invoking its runtime."""

    if isinstance(value, GovernanceReference):
        if value.generation and value.generation != generation:
            raise ValueError("reference generation does not match its source")
        return GovernanceReference(
            value.identifier,
            value.version,
            value.uri,
            value.kind,
            generation,
            value.metadata,
        )
    identifier = value.get("identifier")
    if not isinstance(identifier, str):
        raise ValueError("aggregated metadata requires a string identifier")
    version = value.get("version", "")
    uri = value.get("uri", "")
    kind = value.get("kind", "metadata")
    metadata = value.get("metadata", {})
    if (
        not isinstance(version, str)
        or not isinstance(uri, str)
        or not isinstance(kind, str)
    ):
        raise ValueError("reference version, uri, and kind must be strings")
    if not isinstance(metadata, Mapping):
        raise ValueError("reference metadata must be a mapping")
    return GovernanceReference(
        identifier, version, uri, kind, generation, metadata
    )


class PolicyFabric:
    """Reference-only aggregation for V6, V7, and V8 governance metadata."""

    SOURCE_NAMES = ("v6_governance", "v7_frameworks", "v8_frameworks")

    def aggregate(
        self,
        *,
        v6_governance: tuple[
            GovernanceReference | Mapping[str, object], ...
        ] = (),
        v7_frameworks: tuple[
            GovernanceReference | Mapping[str, object], ...
        ] = (),
        v8_frameworks: tuple[
            GovernanceReference | Mapping[str, object], ...
        ] = (),
    ) -> dict[str, tuple[GovernanceReference, ...]]:
        return {
            "v6_governance": tuple(
                normalize_reference(item, "v6") for item in v6_governance
            ),
            "v7_frameworks": tuple(
                normalize_reference(item, "v7") for item in v7_frameworks
            ),
            "v8_frameworks": tuple(
                normalize_reference(item, "v8") for item in v8_frameworks
            ),
        }

    @staticmethod
    def enforces_policies() -> bool:
        return False

    @staticmethod
    def mutates_runtime_state() -> bool:
        return False


def authorizes_execution(_: object) -> bool:
    """Governance metadata never authorizes execution."""

    return False


__all__ = ("PolicyFabric", "authorizes_execution", "normalize_reference")
