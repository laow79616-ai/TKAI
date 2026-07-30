"""Stable V9 metric names."""

from tkai.v9.meta_kernel import METRIC_NAMES

METRICS = tuple(f"v9_meta_kernel_{name}" for name in METRIC_NAMES)
__all__ = ("METRICS",)
