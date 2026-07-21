from tkai.generators.hooks import HookManager


def test_register():
    manager = HookManager()

    def func():
        return 1

    manager.register("pre_generate", func)

    assert manager.has("pre_generate")


def test_run():
    manager = HookManager()

    def hello(name):
        return f"Hello {name}"

    manager.register("post_generate", hello)

    result = manager.run(
        "post_generate",
        "TKAI",
    )

    assert result == ["Hello TKAI"]


def test_unregister():
    manager = HookManager()

    def func():
        return 1

    manager.register("x", func)
    manager.unregister("x", func)

    assert not manager.has("x")


def test_clear():
    manager = HookManager()

    manager.register(
        "a",
        lambda: None,
    )

    manager.clear()

    assert manager.events() == []