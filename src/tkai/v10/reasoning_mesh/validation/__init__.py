"""Deterministic bounded validation for reasoning metadata."""

from dataclasses import fields, is_dataclass

from tkai.v10.reasoning_mesh.contracts import Confidence, ReasoningContext

MAX_RESULT_SIZE = 100
MAX_REFERENCES = 1_000


def validate_record(record: object) -> None:
    if (
        isinstance(record, Confidence)
        and record.value is not None
        and not 0 <= record.value <= 1
    ):
        raise ValueError("confidence value must be between 0 and 1")
    if isinstance(record, ReasoningContext) and record.time_range is not None:
        start, end = record.time_range
        if start > end:
            raise ValueError("time range must be ordered")
    if is_dataclass(record) and not isinstance(record, type):
        for item in fields(record):
            value = getattr(record, item.name)
            if isinstance(value, tuple) and len(value) > MAX_REFERENCES:
                raise ValueError(f"{item.name} exceeds bounded reference count")


__all__ = ("MAX_REFERENCES", "MAX_RESULT_SIZE", "validate_record")
