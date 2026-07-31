"""Read-only cross-version reference catalog."""

SUPPORTED_GENERATIONS = ("v6", "v7", "v8", "v9", "v10", "v11")
V10_REFERENCES = {
    "sovereign_core": "v10:sovereign-core",
    "trust": "v10:trust-mesh",
    "integrity": "v10:integrity-mesh",
    "governance": "v10:governance-mesh",
    "compatibility": "v10:compatibility-mesh",
    "knowledge": "v10:knowledge-mesh",
    "reasoning": "v10:reasoning-mesh",
    "decision": "v10:decision-mesh",
    "planning": "v10:planning-mesh",
    "operations": "v10:operations-mesh",
    "recovery": "v10:recovery-mesh",
}


def compatibility_projection() -> dict[str, object]:
    return {
        "supported_generations": SUPPORTED_GENERATIONS,
        "v10_references": dict(V10_REFERENCES),
        "integration": "read-only-reference",
        "backward_compatible": True,
        "mutation": False,
    }


__all__ = ("SUPPORTED_GENERATIONS", "V10_REFERENCES", "compatibility_projection")
