from tkai.core.context import Context


def test_context_default():
    ctx = Context()

    assert ctx.project is None
    assert ctx.workspace is None
    assert ctx.settings is None
    assert ctx.logger is None
    assert ctx.runtime == {}
    assert ctx.environment == {}
    assert ctx.services == {}


def test_set_get():
    ctx = Context()

    ctx.set("a", 100)

    assert ctx.get("a") == 100
    assert ctx.has("a")


def test_remove():
    ctx = Context()

    ctx.set("a", 1)

    assert ctx.remove("a") == 1
    assert not ctx.has("a")


def test_clear():
    ctx = Context()

    ctx.set("a", 1)
    ctx.runtime["debug"] = True

    ctx.clear()

    assert ctx.services == {}
    assert ctx.runtime == {}


def test_inject():
    ctx = Context()

    project = object()
    workspace = object()

    ctx.inject(
        project=project,
        workspace=workspace,
    )

    assert ctx.project is project
    assert ctx.workspace is workspace