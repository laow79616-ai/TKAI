from pathlib import Path

from tkai.generators.renderer import TemplateRenderer


def test_render_string():
    renderer = TemplateRenderer()

    result = renderer.render_string(
        "Hello {{ name }}",
        {"name": "TKAI"},
    )

    assert result == "Hello TKAI"


def test_render_file(tmp_path: Path):
    template = tmp_path / "hello.txt"

    template.write_text(
        "Hi {{ user }}",
        encoding="utf-8",
    )

    renderer = TemplateRenderer(tmp_path)

    result = renderer.render_file(
        "hello.txt",
        {"user": "Alice"},
    )

    assert result == "Hi Alice"


def test_render_to_file(tmp_path: Path):
    template = tmp_path / "demo.txt"

    template.write_text(
        "{{ project }}",
        encoding="utf-8",
    )

    renderer = TemplateRenderer(tmp_path)

    output = tmp_path / "output.txt"

    renderer.render_to_file(
        "demo.txt",
        output,
        {"project": "TKAI"},
    )

    assert output.exists()
    assert output.read_text(encoding="utf-8") == "TKAI"


def test_add_filter():
    renderer = TemplateRenderer()

    renderer.add_filter(
        "upper",
        lambda s: s.upper(),
    )

    result = renderer.render_string(
        "{{ name|upper }}",
        {"name": "tkai"},
    )

    assert result == "TKAI"