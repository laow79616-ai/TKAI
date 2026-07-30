from tkai.v8.hyper_reasoning.contracts import ConfidenceMetadata


def validate_probability(value: float | None) -> float | None:
    if value is not None and not 0 <= value <= 1:
        raise ValueError("confidence value must be between 0 and 1")
    return value


__all__ = ("ConfidenceMetadata", "validate_probability")
