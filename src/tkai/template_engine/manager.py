from pathlib import Path
import json


class TemplateManager:
    """
    Manage TKAI project templates.
    """

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

                templates.append({
                    "name": template_dir.name,
                    "description": "No description"
                })

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