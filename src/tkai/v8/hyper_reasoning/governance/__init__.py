"""Governance references only; this fabric never approves execution."""


def authorizes_execution() -> bool:
    return False


__all__ = ("authorizes_execution",)
