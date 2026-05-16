"""Command palette — Ctrl+P fuzzy command launcher."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Input, Label, ListItem, ListView, Static
from textual.containers import Vertical


@dataclass
class Command:
    label: str
    description: str
    action: str  # action name to call on app
    icon: str = "›"


COMMANDS: list[Command] = [
    Command("New Chat", "Start a fresh conversation", "new_session", "💬"),
    Command("Settings", "Open settings panel", "action_settings", "⚙"),
    Command("Switch Provider", "Change AI provider", "switch_provider", "🔌"),
    Command("Switch Model", "Change AI model", "switch_model", "🧠"),
    Command("Usage Report", "Show token/cost analytics", "show_usage", "📊"),
    Command("Export Session", "Export current session as Markdown", "export_session", "📤"),
    Command("Search Memory", "Search conversation history", "search_memory", "🔍"),
    Command("Toggle Sidebar", "Show/hide sidebar", "toggle_sidebar", "◀"),
    Command("Clear Chat", "Clear current chat display", "clear_chat", "🗑"),
    Command("Doctor", "Check clob installation", "run_doctor", "🩺"),
    Command("Quit", "Exit clob", "quit", "✕"),
]


class CommandItem(ListItem):
    def __init__(self, cmd: Command, **kwargs) -> None:
        super().__init__(**kwargs)
        self.cmd = cmd

    def compose(self) -> ComposeResult:
        yield Static(
            f"{self.cmd.icon}  [bold]{self.cmd.label}[/bold]  [dim]{self.cmd.description}[/dim]"
        )


class CommandPalette(ModalScreen[str | None]):
    """Ctrl+P command palette."""

    DEFAULT_CSS = """
    CommandPalette {
        align: center top;
        padding-top: 3;
    }
    #palette-container {
        background: #161b22;
        border: solid #30363d;
        width: 70;
        height: auto;
        max-height: 30;
    }
    #palette-input {
        background: #0d1117;
        border: solid #1f6feb;
        color: #e6edf3;
        height: 3;
        padding: 0 1;
        margin: 1 1 0 1;
    }
    #palette-list {
        height: auto;
        max-height: 20;
        margin: 0 1 1 1;
        background: #161b22;
    }
    CommandItem {
        padding: 0 1;
        height: 2;
    }
    CommandItem:hover {
        background: #21262d;
    }
    CommandItem.--highlight {
        background: #1f6feb22;
    }
    #palette-hint {
        color: #8b949e;
        height: 2;
        padding: 0 1;
        border-top: solid #30363d;
        content-align: left middle;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss_none", "Close"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._filtered = list(COMMANDS)

    def compose(self) -> ComposeResult:
        with Vertical(id="palette-container"):
            yield Input(placeholder="Search commands…", id="palette-input")
            yield ListView(id="palette-list")
            yield Label("↑↓ navigate  Enter select  Esc close", id="palette-hint")

    def on_mount(self) -> None:
        self._populate(COMMANDS)
        self.query_one("#palette-input", Input).focus()

    def _populate(self, cmds: list[Command]) -> None:
        lv = self.query_one("#palette-list", ListView)
        lv.clear()
        for cmd in cmds:
            lv.append(CommandItem(cmd))

    def on_input_changed(self, event: Input.Changed) -> None:
        q = event.value.lower().strip()
        filtered = [c for c in COMMANDS if q in c.label.lower() or q in c.description.lower()]
        self._populate(filtered)
        self._filtered = filtered

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, CommandItem):
            self.dismiss(event.item.cmd.action)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        lv = self.query_one("#palette-list", ListView)
        if lv.highlighted_child and isinstance(lv.highlighted_child, CommandItem):
            self.dismiss(lv.highlighted_child.cmd.action)
        elif self._filtered:
            self.dismiss(self._filtered[0].action)
        else:
            self.dismiss(None)

    def action_dismiss_none(self) -> None:
        self.dismiss(None)
