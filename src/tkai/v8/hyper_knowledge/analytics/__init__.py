"""Pure metadata coverage analytics."""

from tkai.v8.hyper_knowledge.fabric import HyperKnowledgeFabric


def coverage_summary(fabric: HyperKnowledgeFabric) -> dict[str, object]:
    metrics = fabric.metrics()
    return {
        "profiles": metrics["profiles"],
        "ontology": metrics["ontology"],
        "evidence": metrics["evidence"],
        "lineage": metrics["lineage"],
        "reference_only": True,
    }


__all__ = ("coverage_summary",)
