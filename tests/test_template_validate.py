import json
from pathlib import Path

import pytest

from tkai.template_engine import TemplateManager


def create_template(root: Path, name: str, data: dict):
    template_dir = root / name
    template_dir.mkdir(parents=True, exist_ok=True)

    with open(template_dir / "template.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def test_validate_template_success(tmp_path):
    create_template(
        tmp_path,
        "fastapi",
        {
            "name": "fastapi",
            "description": "FastAPI Template",
            "version": "1.0.0",
        },
    )

    manager = TemplateManager()
    manager.templates_dir = tmp_path

    result = manager.validate_template("fastapi")

    assert result["valid"] is True
    assert result["errors"] == []


def test_validate_template_missing_file(tmp_path):
    (tmp_path / "fastapi").mkdir()

    manager = TemplateManager()
    manager.templates_dir = tmp_path

    result = manager.validate_template("fastapi")

    assert result["valid"] is False
    assert "template.json not found" in result["errors"]


def test_validate_template_invalid_json(tmp_path):
    template_dir = tmp_path / "fastapi"
    template_dir.mkdir()

    with open(template_dir / "template.json", "w", encoding="utf-8") as f:
        f.write("{invalid json}")

    manager = TemplateManager()
    manager.templates_dir = tmp_path

    result = manager.validate_template("fastapi")

    assert result["valid"] is False
    assert any("Invalid JSON" in error for error in result["errors"])


@pytest.mark.parametrize(
    "field",
    [
        "name",
        "description",
        "version",
    ],
)
def test_validate_template_missing_required_field(tmp_path, field):
    data = {
        "name": "fastapi",
        "description": "FastAPI Template",
        "version": "1.0.0",
    }

    data.pop(field)

    create_template(tmp_path, "fastapi", data)

    manager = TemplateManager()
    manager.templates_dir = tmp_path

    result = manager.validate_template("fastapi")

    assert result["valid"] is False
    assert f"Missing field: {field}" in result["errors"]


def test_validate_all(tmp_path):
    create_template(
        tmp_path,
        "fastapi",
        {
            "name": "fastapi",
            "description": "FastAPI Template",
            "version": "1.0.0",
        },
    )

    create_template(
        tmp_path,
        "broken",
        {
            "name": "broken",
            "description": "Broken Template",
        },
    )

    manager = TemplateManager()
    manager.templates_dir = tmp_path

    results = manager.validate_all()

    assert len(results) == 2

    assert any(item["name"] == "fastapi" and item["valid"] for item in results)

    assert any(
        item["name"] == "broken"
        and not item["valid"]
        for item in results
    )