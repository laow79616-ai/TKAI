"""V6/V7/V8 governance compatibility metadata."""

from tkai.v8.hyper_governance.contracts import CompatibilityRecord

SUPPORTED_GENERATIONS = ("v6", "v7", "v8")

__all__ = ("CompatibilityRecord", "SUPPORTED_GENERATIONS")
