from pathlib import Path

from tkai.generators.engine import GeneratorEngine


def test_engine_generate(tmp_path: Path):
    template = tmp_path / "template"
    template.mkdir()

    (template / "README.md.j2").write_text(
        "# {{ project }}",
        encoding="utf-8",
    )

    engine = GeneratorEngine(template)

    output = tmp_path / "demo"

    result = engine.generate(
        output,
        {
            "project": "TKAI",
        },
    )

    assert result.exists()
    assert (output / "README.md").exists()
    assert (
        output / "README.md"
    ).read_text(encoding="utf-8") == "# TKAI"


def test_engine_hooks(tmp_path: Path):
    template = tmp_path / "template"
    template.mkdir()

    (template / "demo.txt.j2").write_text(
        "{{ name }}",
        encoding="utf-8",
    )

    called = []

    def before(_):
        called.append("before")

    def after(*_):
        called.append("after")

    engine = GeneratorEngine(template)

    engine.register_hook(
        "pre_generate",
        before,
    )

    engine.register_hook(
        "post_generate",
        after,
    )

    engine.generate(
        tmp_path / "output",
        {
            "name": "TKAI",
        },
    )

    assert called == [
        "before",
        "after",
    ]


def test_missing_template():
    import pytest

    with pytest.raises(FileNotFoundError):
        GeneratorEngine("not_exists")