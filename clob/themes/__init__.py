"""Theming system for clob TUI.

Themes define TCSS variables, syntax colors, and panel styles.
Users can place custom themes in ~/.config/clob/themes/
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config.settings import CONFIG_DIR

THEMES_DIR = CONFIG_DIR / "themes"
BUILTIN_THEMES_DIR = Path(__file__).parent / "builtin"


@dataclass
class Theme:
    name: str
    description: str
    tcss: str


BUILTIN: dict[str, Theme] = {
    "dark": Theme(
        name="dark",
        description="Default dark theme (GitHub-inspired)",
        tcss="""
Screen { background: #0d1117; color: #e6edf3; }
#sidebar { background: #161b22; border-right: solid #30363d; }
#sidebar-title { color: #58a6ff; }
.session-item { color: #8b949e; }
.session-item:hover { background: #21262d; color: #e6edf3; }
.session-item.--highlight { background: #1f6feb33; color: #58a6ff; }
#chat-scroll { background: #0d1117; }
#input-area { background: #161b22; border-top: solid #30363d; }
#prompt-input { background: #0d1117; border: solid #30363d; color: #e6edf3; }
#prompt-input:focus { border: solid #1f6feb; }
Button.primary { background: #1f6feb; color: white; }
""",
    ),
    "light": Theme(
        name="light",
        description="Clean light theme",
        tcss="""
Screen { background: #ffffff; color: #24292f; }
#sidebar { background: #f6f8fa; border-right: solid #d0d7de; }
#sidebar-title { color: #0969da; }
.session-item { color: #57606a; }
.session-item:hover { background: #eaeef2; color: #24292f; }
.session-item.--highlight { background: #ddf4ff; color: #0969da; }
#chat-scroll { background: #ffffff; }
#input-area { background: #f6f8fa; border-top: solid #d0d7de; }
#prompt-input { background: #ffffff; border: solid #d0d7de; color: #24292f; }
#prompt-input:focus { border: solid #0969da; }
Button.primary { background: #0969da; color: white; }
""",
    ),
    "cyberpunk": Theme(
        name="cyberpunk",
        description="Neon cyberpunk aesthetic",
        tcss="""
Screen { background: #0a0a0f; color: #00ff9f; }
#sidebar { background: #0d0d1a; border-right: solid #ff00ff; }
#sidebar-title { color: #ff00ff; text-style: bold; }
.session-item { color: #00ccff; }
.session-item:hover { background: #1a0033; color: #ff00ff; }
.session-item.--highlight { background: #00ff9f22; color: #00ff9f; }
#chat-scroll { background: #0a0a0f; }
#input-area { background: #0d0d1a; border-top: solid #ff00ff; }
#prompt-input { background: #0a0a0f; border: solid #00ccff; color: #00ff9f; }
#prompt-input:focus { border: solid #ff00ff; }
Button.primary { background: #ff00ff; color: #0a0a0f; }
""",
    ),
    "nord": Theme(
        name="nord",
        description="Nord color palette",
        tcss="""
Screen { background: #2e3440; color: #eceff4; }
#sidebar { background: #3b4252; border-right: solid #4c566a; }
#sidebar-title { color: #88c0d0; }
.session-item { color: #d8dee9; }
.session-item:hover { background: #434c5e; color: #eceff4; }
.session-item.--highlight { background: #5e81ac44; color: #88c0d0; }
#chat-scroll { background: #2e3440; }
#input-area { background: #3b4252; border-top: solid #4c566a; }
#prompt-input { background: #2e3440; border: solid #4c566a; color: #eceff4; }
#prompt-input:focus { border: solid #88c0d0; }
Button.primary { background: #5e81ac; color: white; }
""",
    ),
}


def get_theme(name: str) -> Theme:
    """Get a theme by name, checking builtins then user themes dir."""
    if name in BUILTIN:
        return BUILTIN[name]

    # Check user themes dir
    user_path = THEMES_DIR / f"{name}.tcss"
    if user_path.exists():
        tcss = user_path.read_text()
        return Theme(name=name, description="User theme", tcss=tcss)

    return BUILTIN["dark"]


def list_themes() -> list[str]:
    names = list(BUILTIN.keys())
    if THEMES_DIR.exists():
        for f in THEMES_DIR.glob("*.tcss"):
            if f.stem not in names:
                names.append(f.stem)
    return names
