from tkai.core.context import Context
from tkai.core.exceptions import GeneratorError
from tkai.generators.base import BaseGenerator
from tkai.generators.generator import GeneratorManager


class DemoGenerator(BaseGenerator):

    def generate(self, **kwargs):
        return kwargs.get("name", "ok")


def test_register():
    ctx = Context()
    manager = GeneratorManager(ctx)

    gen = DemoGenerator(ctx)

    manager.register(gen)

    assert manager.count() == 1
    assert manager.has("DemoGenerator")


def test_duplicate():
    ctx = Context()
    manager = GeneratorManager(ctx)

    gen = DemoGenerator(ctx)

    manager.register(gen)

    try:
        manager.register(gen)
        assert False
    except GeneratorError:
        assert True


def test_get():
    ctx = Context()
    manager = GeneratorManager(ctx)

    gen = DemoGenerator(ctx)

    manager.register(gen)

    assert manager.get("DemoGenerator") is gen


def test_generate():
    ctx = Context()
    manager = GeneratorManager(ctx)

    gen = DemoGenerator(ctx)

    manager.register(gen)

    assert manager.generate(
        "DemoGenerator",
        name="tkai",
    ) == "tkai"


def test_unregister():
    ctx = Context()
    manager = GeneratorManager(ctx)

    gen = DemoGenerator(ctx)

    manager.register(gen)

    manager.unregister("DemoGenerator")

    assert manager.count() == 0


def test_clear():
    ctx = Context()
    manager = GeneratorManager(ctx)

    manager.register(DemoGenerator(ctx))

    manager.clear()

    assert manager.count() == 0