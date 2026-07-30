from tkai.v8.hyper_reasoning.fabric import HyperReasoningFabric


def diagnostics(fabric: HyperReasoningFabric) -> tuple[dict[str, object], ...]:
    return fabric.diagnostics()


__all__ = ("diagnostics",)
