"""Plugin loader — dynamically load clob plugins."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

from ..config.settings import CONFIG_DIR


PLUGINS_DIR = CONFIG_DIR / "plugins"


class Plugin:
    """Base class for clob plugins."""

    name: str = "unnamed"
    version: str = "0.1.0"
    description: str = ""

    def on_load(self, app: Any) -> None:
        """Called when plugin is loaded."""
        pass

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        pass


class PluginLoader:
    """Loads and manages plugins from ~/.config/clob/plugins/."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def load_all(self) -> list[str]:
        """Load all plugins from the plugins directory."""
        loaded = []
        if not PLUGINS_DIR.exists():
            return loaded

        for plugin_path in PLUGINS_DIR.glob("*/plugin.py"):
            name = plugin_path.parent.name
            try:
                plugin = self._load_file(name, plugin_path)
                self._plugins[name] = plugin
                loaded.append(name)
            except Exception as e:
                print(f"[clob] Failed to load plugin '{name}': {e}")

        return loaded

    def _load_file(self, name: str, path: Path) -> Plugin:
        spec = importlib.util.spec_from_file_location(f"clob_plugin_{name}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugin_cls = getattr(module, "ClobPlugin", Plugin)
        return plugin_cls()

    def get(self, name: str) -> Plugin | None:
        return self._plugins.get(name)

    def list_plugins(self) -> list[str]:
        return list(self._plugins.keys())


plugin_loader = PluginLoader()
