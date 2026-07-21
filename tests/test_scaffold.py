from pathlib import Path

from tkai.generators.scaffold import Scaffold


def test_generate_project(tmp_path: Path):
    template = tmp_path / "template"
    template.mkdir()

    (template / "README.md.j2").write_text(
        "# {{ project }}",
        encoding="utf-8",
    )

    (template / "{{ project_name }}.txt.j2").write_text(
        "{{ author }}",
        encoding="utf-8",
    )

    output = tmp_path / "output"

    scaffold = Scaffold(template)

    scaffold.generate(
        output,
        {
            "project": "TKAI",
            "project_name": "demo",
            "author": "wang",
        },
    )

    assert (output / "README.md").exists()
    assert (output / "demo.txt").exists()

    assert (
        output / "README.md"
    ).read_text() == "# TKAI"

    assert (
        output / "demo.txt"
    ).read_text() == "wang"