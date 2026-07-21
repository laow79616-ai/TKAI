from tkai.core.lifecycle import Lifecycle, LifecycleState


def test_default_state():
    lifecycle = Lifecycle()

    assert lifecycle.state is LifecycleState.CREATED
    assert lifecycle.is_created


def test_initialize():
    lifecycle = Lifecycle()

    lifecycle.initialize()

    assert lifecycle.state is LifecycleState.INITIALIZED
    assert lifecycle.is_initialized


def test_start():
    lifecycle = Lifecycle()

    lifecycle.initialize()
    lifecycle.start()

    assert lifecycle.state is LifecycleState.STARTED
    assert lifecycle.is_started


def test_stop():
    lifecycle = Lifecycle()

    lifecycle.start()
    lifecycle.stop()

    assert lifecycle.state is LifecycleState.STOPPED
    assert lifecycle.is_stopped


def test_dispose():
    lifecycle = Lifecycle()

    lifecycle.dispose()

    assert lifecycle.state is LifecycleState.DISPOSED
    assert lifecycle.is_disposed