"""Memory search modal screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static


class MemorySearchScreen(ModalScreen):
    """Search conversation history."""

    DEFAULT_CSS = """
    MemorySearchScreen {
        align: center middle;
    }
    #search-dialog {
        background: #161b22;
        border: solid #30363d;
        padding: 2 3;
        width: 70;
        height: 30;
    }
    #search-title {
        color: #58a6ff;
        text-style: bold;
        margin-bottom: 1;
    }
    #search-input {
        background: #0d1117;
        border: solid #1f6feb;
        color: #e6edf3;
        height: 3;
        margin-bottom: 1;
    }
    #results-list {
        height: 18;
        background: #0d1117;
        border: solid #30363d;
    }
    .result-item {
        padding: 0 1;
        height: 3;
        color: #e6edf3;
    }
    .result-item:hover {
        background: #21262d;
    }
    #search-buttons {
        height: 3;
        margin-top: 1;
        align: right middle;
    }
    """

    BINDINGS = [Binding("escape", "dismiss", "Close")]

    def __init__(self, memory_manager, **kwargs) -> None:
        super().__init__(**kwargs)
        self.memory = memory_manager

    def compose(self) -> ComposeResult:
        with Vertical(id="search-dialog"):
            yield Label("🔍  Search Memory", id="search-title")
            yield Input(placeholder="Search conversations…", id="search-input")
            yield ListView(id="results-list")
            with Horizontal(id="search-buttons"):
                yield Button("Close", id="close-btn")

    def on_mount(self) -> None:
        self.query_one("#search-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input" and len(event.value) >= 2:
            self.app.call_later(self._do_search, event.value)

    async def _do_search(self, query: str) -> None:
        results = await self.memory.search(query)
        lv = self.query_one("#results-list", ListView)
        lv.clear()
        if not results:
            lv.append(ListItem(Static("[dim]No results found[/dim]")))
        for msg in results[:15]:
            preview = msg.content[:60].replace("\n", " ")
            item = ListItem(Static(f"[{msg.role}] {preview}…"))
            lv.append(item)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()
