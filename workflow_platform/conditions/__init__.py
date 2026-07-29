"""Typed condition evaluation without arbitrary code execution."""

import re
from datetime import datetime
from typing import Any


def evaluate(operator: str, left: Any, right: Any = None) -> bool:
    if operator == "boolean":
        return bool(left)
    if operator == "equals":
        return bool(left == right)
    if operator == "not_equals":
        return bool(left != right)
    if operator in {"greater", "less"}:
        left_number, right_number = float(left), float(right)
        return (
            left_number > right_number
            if operator == "greater"
            else left_number < right_number
        )
    if operator == "regex":
        return re.search(str(right), str(left)) is not None
    if operator == "contains":
        return str(right) in str(left)
    if operator in {"before", "after"}:
        left_date = datetime.fromisoformat(str(left))
        right_date = datetime.fromisoformat(str(right))
        return (
            left_date < right_date if operator == "before" else left_date > right_date
        )
    raise ValueError("Unsupported condition operator.")


def switch(value: Any, cases: dict[Any, str], default: str) -> str:
    return cases.get(value, default)
