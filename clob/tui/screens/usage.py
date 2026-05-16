"""Usage analytics modal screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from textual.containers import Vertical


class UsageScreen(ModalScreen):
    """Display token/cost analytics."""

    DEFAULT_CSS = """
    UsageScreen {
        align: center middle;
    }
    #usage-dialog {
        background: #161b22;
        border: solid #30363d;
        padding: 2 3;
        width: 55;
        height: auto;
    }
    #usage-title {
        color: #58a6ff;
        text-style: bold;
        margin-bottom: 1;
    }
    #usage-content {
        color: #e6edf3;
        margin-bottom: 1;
    }
    #usage-close {
        margin-top: 1;
    }
    """

    BINDINGS = [Binding("escape", "dismiss", "Close")]

    def __init__(self, report: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.report = report

    def compose(self) -> ComposeResult:
        with Vertical(id="usage-dialog"):
            yield Label("📊  Usage Report", id="usage-title")
            yield Static(self.report, id="usage-content")
            yield Button("Close", id="usage-close", classes="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()
