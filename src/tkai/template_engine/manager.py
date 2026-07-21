from pathlib import Path
import json
from json import JSONDecodeError


class TemplateManager:
    """
    Manage TKAI project templates.
    """

    REQUIRED_FIELDS = (
        "name",
        "description",
        "version",
    )

    def __init__(self):
        self.root = Path(__file__).resolve().parents[3]
        self.templates_dir = self.root / "templates"

    def list_templates(self):
        """
        Return all available templates.
        """

        templates = []

        if not self.templates_dir.exists():
            return templates

        for template_dir in self.templates_dir.iterdir():

            if not template_dir.is_dir():
                continue

            manifest = template_dir / "template.json"

            if manifest.exists():

                with open(manifest, "r", encoding="utf-8") as f:
                    templates.append(json.load(f))

            else:

                templates.append(
                    {
                        "name": template_dir.name,
                        "description": "No description",
                    }
                )

        return templates

    def get_template(self, name: str):
        """
        Return one template metadata.
        """

        manifest = self.templates_dir / name / "template.json"

        if not manifest.exists():
            raise FileNotFoundError(
                f"Template '{name}' not found."
            )

        with open(manifest, "r", encoding="utf-8") as f:
            return json.load(f)

    def validate_template(self, name: str):
        """
        Validate a single template.
        """

        manifest = self.templates_dir / name / "template.json"

        result = {
            "name": name,
            "valid": True,
            "errors": [],
        }

        if not manifest.exists():
            result["valid"] = False
            result["errors"].append("template.json not found")
            return result

        try:
            with open(manifest, "r", encoding="utf-8") as f:
                metadata = json.load(f)

        except JSONDecodeError as exc:
            result["valid"] = False
            result["errors"].append(f"Invalid JSON: {exc}")
            return result

        except Exception as exc:
            result["valid"] = False
            result["errors"].append(str(exc))
            return result

        for field in self.REQUIRED_FIELDS:
            if field not in metadata:
                result["valid"] = False
                result["errors"].append(
                    f"Missing field: {field}"
                )

        return result

    def validate_all(self):
        """
        Validate every template.
        """

        results = []

        if not self.templates_dir.exists():
            return results

        for template_dir in sorted(self.templates_dir.iterdir()):

            if not template_dir.is_dir():
                continue

            results.append(
                self.validate_template(template_dir.name)
            )

        return results