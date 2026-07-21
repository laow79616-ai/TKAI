from tkai.generators.variables import VariableManager


def test_set_get():
    manager = VariableManager()

    manager.set("name", "demo")

    assert manager.get("name") == "demo"


def test_default():
    manager = VariableManager()

    manager.set_default("author", "wang")

    assert manager.get("author") == "wang"


def test_remove():
    manager = VariableManager()

    manager.set("name", "demo")

    manager.remove("name")

    assert not manager.has("name")


def test_update():
    manager = VariableManager()

    manager.update(
        {
            "name": "demo",
            "version": "1.0.0",
        }
    )

    assert manager.get("version") == "1.0.0"


def test_merge():
    manager = VariableManager()

    manager.set("author", "wang")

    manager.merge(
        {"name": "demo"},
        {"version": "1.0.0"},
    )

    assert manager.get("author") == "wang"
    assert manager.get("name") == "demo"
    assert manager.get("version") == "1.0.0"


def test_to_dict():
    manager = VariableManager()

    manager.set("name", "demo")

    data = manager.to_dict()

    assert data["name"] == "demo"


def test_from_dict():
    manager = VariableManager.from_dict(
        {
            "name": "demo",
            "author": "wang",
        }
    )

    assert manager.get("author") == "wang"


def test_clear():
    manager = VariableManager()

    manager.set("name", "demo")

    manager.clear()

    assert len(manager) == 0