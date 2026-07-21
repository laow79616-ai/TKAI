from pathlib import Path

import yaml

from tkai.config.saver import ConfigSaver


def test_save_yaml(tmp_path: Path):
    path = tmp_path / "config.yaml"

    config = {
        "language": "en-US",
        "template": "fastapi",
        "llm": {
            "provider": "openai",
            "model": "gpt-5.5",
        },
    }

    ConfigSaver.save(path, config)

    assert path.exists()

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data == config


def test_save_creates_directory(tmp_path: Path):
    path = tmp_path / "config" / "config.yaml"

    config = {
        "language": "zh-CN",
    }

    ConfigSaver.save(path, config)

    assert path.exists()

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["language"] == "zh-CN"


def test_save_overwrite(tmp_path: Path):
    path = tmp_path / "config.yaml"

    ConfigSaver.save(
        path,
        {
            "language": "zh-CN",
        },
    )

    ConfigSaver.save(
        path,
        {
            "language": "en-US",
        },
    )

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["language"] == "en-US"


def test_save_project(tmp_path: Path):
    config = {
        "template": "fastapi",
    }

    ConfigSaver.save_project(config, tmp_path)

    path = tmp_path / ".tkai" / "config.yaml"

    assert path.exists()

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["template"] == "fastapi"