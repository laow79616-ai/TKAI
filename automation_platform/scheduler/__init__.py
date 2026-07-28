"""Scheduler contracts."""

from automation_platform.platform import Schedule

SCHEDULE_KINDS = ("cron", "interval", "calendar")
MISSED_EXECUTION_POLICIES = ("skip", "run_once", "catch_up")
__all__ = ("MISSED_EXECUTION_POLICIES", "SCHEDULE_KINDS", "Schedule")
