from tkai.core.exceptions import RegistryError
from tkai.core.registry import Registry


def test_register():
    registry = Registry()

    registry.register("demo", object())

    assert registry.has("demo")
    assert registry.count() == 1


def test_duplicate_register():
    registry = Registry()

    registry.register("demo", object())

    try:
        registry.register("demo", object())
        assert False
    except RegistryError:
        assert True


def test_unregister():
    registry = Registry()

    registry.register("demo", 1)

    assert registry.unregister("demo") == 1
    assert registry.count() == 0


def test_get():
    registry = Registry()

    registry.register("demo", 100)

    assert registry.get("demo") == 100


def test_missing():
    registry = Registry()

    try:
        registry.get("none")
        assert False
    except RegistryError:
        assert True


def test_clear():
    registry = Registry()

    registry.register("a", 1)
    registry.register("b", 2)

    registry.clear()

    assert registry.count() == 0


def test_names_values_items():
    registry = Registry()

    registry.register("a", 1)
    registry.register("b", 2)

    assert registry.names() == ["a", "b"]
    assert registry.values() == [1, 2]
    assert len(registry.items()) == 2


def test_magic_methods():
    registry = Registry()

    registry.register("demo", 1)

    assert "demo" in registry
    assert len(registry) == 1
    assert registry["demo"] == 1