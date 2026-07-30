from tkai.v8.hyper_reasoning.contracts import Recommendation


def authorizes_execution(value: Recommendation) -> bool:
    return value.execution_authorized


__all__ = ("Recommendation", "authorizes_execution")
