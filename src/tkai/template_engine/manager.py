from pathlib import Path
import json


class TemplateManager:
    def __init__(self):
        self.root = Path(__file__).resolve().parents[3]
        self.templates_dir = self.root / "templates"

    def list_templates(self):
        templates = []

        if not self.templates_dir.exists():
            return templates

        for template_dir in self.templates_dir.iterdir():
            if not template_dir.is_dir():
                continue

            manifest = template_dir / "template.json"

            if manifest.exists():
                with open(manifest, "r", encoding="utf-8") as f:
                    data = json.load(f)
                templates.append(data)
            else:
                templates.append({
                    "name": template_dir.name,
                    "description": "No description"
                })

        return templates