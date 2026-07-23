"""High-resolution timer lifecycle checks without sleep-based timing tests."""

import pytest

from benchmarks.timer import HighResolutionTimer, TimerStateError


def test_timer_measures_completed_lifecycle() -> None:
    timer = HighResolutionTimer().start()
    elapsed = timer.stop()
    assert elapsed >= 0
    assert timer.elapsed_ns == elapsed
    assert timer.elapsed_seconds >= 0.0


def test_timer_rejects_invalid_lifecycle_calls() -> None:
    timer = HighResolutionTimer()
    with pytest.raises(TimerStateError):
        timer.stop()
    with pytest.raises(TimerStateError):
        _ = timer.elapsed_ns
    timer.start()
    with pytest.raises(TimerStateError):
        timer.start()
    timer.stop()
    with pytest.raises(TimerStateError):
        timer.stop()
