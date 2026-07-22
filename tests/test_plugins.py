import json
from pathlib import Path

import pytest

from tkai.core.context import Context
from tkai.core.exceptions import PluginError
from tkai.plugins import PluginManager, PluginManifest


def _create_plugin(root: Path, *, enabled: bool = True) -> Path:
    plugin_dir = root / "demo"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.json").write_text(
        json.dumps(
            {
                "name": "demo",
                "version": "1.0.0",
                "entry": "plugin:DemoPlugin",
                "enabled": enabled,
            }
        ),
        encoding="utf-8",
    )
    (plugin_dir / "plugin.py").write_text(
        "class DemoPlugin:\n"
        "    def activate(self, context):\n"
        "        context.set('plugin_active', True)\n"
        "    def deactivate(self, context):\n"
        "        context.remove('plugin_active')\n",
        encoding="utf-8",
    )
    return plugin_dir


def test_manifest_load(tmp_path: Path):
    plugin_dir = _create_plugin(tmp_path)

    manifest = PluginManifest.load(plugin_dir)

    assert manifest.name == "demo"
    assert manifest.entry == "plugin:DemoPlugin"


def test_discover_and_load_plugin(tmp_path: Path):
    plugin_dir = _create_plugin(tmp_path)
    context = Context()
    manager = PluginManager(context)

    assert [manifest.name for manifest in manager.discover(tmp_path)] == ["demo"]

    plugin = manager.load(plugin_dir)

    assert manager.get("demo") is plugin
    assert manager.manifest("demo").version == "1.0.0"
    assert context.get("plugin_active") is True

    assert manager.unload("demo") is plugin
    assert context.has("plugin_active") is False


def test_disabled_plugin_cannot_load(tmp_path: Path):
    plugin_dir = _create_plugin(tmp_path, enabled=False)

    with pytest.raises(PluginError, match="disabled"):
        PluginManager().load(plugin_dir)
