"""Governance reference catalog."""

from __future__ import annotations

from tkai.v8.hyper_coordination.contracts import GovernanceReferences, Reference


def serialize_governance(value: GovernanceReferences) -> dict[str, object]:
    """Serialize external evidence without interpreting it as authority."""

    def serialize(items: tuple[Reference, ...]) -> list[dict[str, object]]:
        return [
            {
                "identifier": item.identifier,
                "version": item.version,
                "uri": item.uri,
                "metadata": dict(item.metadata),
            }
            for item in items
        ]

    return {
        "policies": serialize(value.policies),
        "approvals": serialize(value.approvals),
        "risks": serialize(value.risks),
        "compatibility": serialize(value.compatibility),
        "reviews": serialize(value.reviews),
        "audits": serialize(value.audits),
        "execution_authorized": False,
    }


__all__ = ("GovernanceReferences", "serialize_governance")
