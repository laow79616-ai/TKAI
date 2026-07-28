"""Rollback contracts."""

from automation_platform.platform import RollbackPlan

ROLLBACK_STRATEGIES = ("compensation", "checkpoint_restore", "validation")
__all__ = ("ROLLBACK_STRATEGIES", "RollbackPlan")
