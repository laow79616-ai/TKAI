"""Deterministic bounded validation for planning metadata."""

from dataclasses import fields, is_dataclass

from tkai.v10.planning_mesh.contracts import Timeline

MAX_RESULT_SIZE = 100
MAX_REFERENCES = 1_000


def validate_record(record: object) -> None:
    if (
        isinstance(record, Timeline)
        and record.start_reference is not None
        and record.end_reference is not None
        and record.start_reference > record.end_reference
    ):
        raise ValueError("timeline references must be ordered")
    if is_dataclass(record) and not isinstance(record, type):
        for item in fields(record):
            value = getattr(record, item.name)
            if isinstance(value, tuple) and len(value) > MAX_REFERENCES:
                raise ValueError(f"{item.name} exceeds bounded reference count")


__all__ = ("MAX_REFERENCES", "MAX_RESULT_SIZE", "validate_record")
