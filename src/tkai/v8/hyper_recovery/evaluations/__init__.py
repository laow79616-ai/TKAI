"""Explainable recovery quality evaluations."""

from tkai.v8.hyper_recovery.contracts import Evaluation
from tkai.v8.hyper_recovery.fabric import HyperRecoveryFabric

evaluate = HyperRecoveryFabric.evaluate

__all__ = ("Evaluation", "evaluate")
