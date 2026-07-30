"""Read-only intelligence diagnostics."""

from tkai.v9.intelligence_mesh.fabric import AdaptiveIntelligenceMesh


def diagnostic_snapshot(
    mesh: AdaptiveIntelligenceMesh,
) -> tuple[dict[str, object], ...]:
    return mesh.diagnostics()


__all__ = ("diagnostic_snapshot",)
