from tkai.template_engine.manager import TemplateManager


def test_validate_template_success():
    manager = TemplateManager()

    result = manager.validate_template("fastapi")

    assert result["valid"] is True
    assert result["errors"] == []


def test_validate_template_not_exists():
    manager = TemplateManager()

    result = manager.validate_template("not_exists")

    assert result["valid"] is False
    assert "template.json not found" in result["errors"]


def test_validate_all():
    manager = TemplateManager()

    results = manager.validate_all()

    assert isinstance(results, list)

    assert len(results) >= 1

    for result in results:

        assert "name" in result
        assert "valid" in result
        assert "errors" in result