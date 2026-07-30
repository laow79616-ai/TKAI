from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionEvent:
    name: str
    subject_reference: str
    correlation_id: str = ""


__all__ = ("DecisionEvent",)
