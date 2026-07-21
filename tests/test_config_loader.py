from pathlib import Path

import pytest

from tkai.config.loader import ConfigLoader


def test_load_not_exists(tmp_path: Path):
    path = tmp_path / "config.yaml"

    data = ConfigLoader.load(path)

    assert data == {}


def test_load_yaml(tmp_path: Path):
    path = tmp_path / "config.yaml"

    path.write_text(
        """
language: en-US
template: fastapi
llm:
  provider: openai
  model: gpt-5.5
""",
        encoding="utf-8",
    )

    data = ConfigLoader.load(path)

    assert data["language"] == "en-US"
    assert data["template"] == "fastapi"
    assert data["llm"]["provider"] == "openai"
    assert data["llm"]["model"] == "gpt-5.5"


def test_load_empty_yaml(tmp_path: Path):
    path = tmp_path / "config.yaml"

    path.write_text("", encoding="utf-8")

    data = ConfigLoader.load(path)

    assert data == {}


def test_load_invalid_root(tmp_path: Path):
    path = tmp_path / "config.yaml"

    path.write_text(
        """
- item1
- item2
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        ConfigLoader.load(path)


def test_load_directory(tmp_path: Path):
    with pytest.raises(ValueError):
        ConfigLoader.load(tmp_path)


def test_load_project(tmp_path: Path):
    config_dir = tmp_path / ".tkai"
    config_dir.mkdir()

    config = config_dir / "config.yaml"

    config.write_text(
        """
language: ja-JP
""",
        encoding="utf-8",
    )

    data = ConfigLoader.load_project(tmp_path)

    assert data["language"] == "ja-JP"