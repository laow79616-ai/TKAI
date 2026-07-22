from pathlib import Path

from tkai.templates.manager import TemplateManager


def test_list(tmp_path: Path):

    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()

    manager = TemplateManager(tmp_path)

    assert manager.list() == [
        "a",
        "b",
    ]