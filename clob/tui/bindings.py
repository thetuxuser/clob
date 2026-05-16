"""Keyboard bindings for clob TUI."""

from textual.binding import Binding

APP_BINDINGS = [
    Binding("ctrl+n", "new_session", "New Chat", show=True),
    Binding("ctrl+s", "settings", "Settings", show=True),
    Binding("ctrl+q", "quit", "Quit", show=True),
    Binding("ctrl+l", "clear_chat", "Clear", show=False),
    Binding("ctrl+p", "command_palette", "Commands", show=False),
    Binding("f1", "help", "Help", show=False),
    Binding("escape", "focus_input", "Focus Input", show=False),
]
