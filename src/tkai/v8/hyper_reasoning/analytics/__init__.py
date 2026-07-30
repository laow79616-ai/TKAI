from tkai.v8.hyper_reasoning.fabric import HyperReasoningFabric


def coverage_summary(fabric: HyperReasoningFabric) -> dict[str, object]:
    metrics = fabric.metrics()
    return {
        "evidence": metrics["evidence"],
        "knowledge": metrics["knowledge"],
        "confidence": metrics["confidence"],
        "explanations": metrics["explanations"],
        "reference_only": True,
    }


__all__ = ("coverage_summary",)
