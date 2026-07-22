from pathlib import Path

from tkai.templates.manifest import TemplateManifest


def test_manifest(tmp_path: Path):

    template = tmp_path / "demo"

    template.mkdir()

    (template / "template.yaml").write_text(
        """
name: demo
version: 1.0.0
author: TKAI
description: Demo Template
""",
        encoding="utf-8",
    )

    manifest = TemplateManifest.load(template)

    assert manifest.name == "demo"
    assert manifest.author == "TKAI"