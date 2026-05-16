"""Settings modal screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static
from textual.containers import Vertical, Horizontal


class SettingsScreen(ModalScreen):
    """Settings modal dialog."""

    DEFAULT_CSS = """
    SettingsScreen {
        align: center middle;
    }
    #settings-dialog {
        background: #161b22;
        border: solid #30363d;
        padding: 2 3;
        width: 70;
        height: auto;
        max-height: 40;
    }
    #settings-title {
        color: #58a6ff;
        text-style: bold;
        margin-bottom: 1;
    }
    .setting-row {
        height: 3;
        margin-bottom: 1;
        align: left middle;
    }
    .setting-label {
        width: 20;
        color: #8b949e;
    }
    .setting-input {
        width: 40;
        background: #0d1117;
        border: solid #30363d;
        color: #e6edf3;
    }
    #settings-buttons {
        margin-top: 1;
        align: right middle;
        height: 3;
    }
    """

    def __init__(self, config, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-dialog"):
            yield Label("⚙  Settings", id="settings-title")

            with Horizontal(classes="setting-row"):
                yield Label("Provider:", classes="setting-label")
                provider_opts = [(p, p) for p in (self.config.providers.keys() or ["openrouter"])]
                yield Select(
                    provider_opts,
                    value=self.config.default.provider,
                    id="provider-select",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Model:", classes="setting-label")
                yield Input(
                    value=self.config.default.model,
                    placeholder="e.g. openai/gpt-4o-mini",
                    id="model-input",
                    classes="setting-input",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Max Tokens:", classes="setting-label")
                yield Input(
                    value=str(self.config.default.max_tokens),
                    id="max-tokens-input",
                    classes="setting-input",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Temperature:", classes="setting-label")
                yield Input(
                    value=str(self.config.default.temperature),
                    id="temperature-input",
                    classes="setting-input",
                )

            with Horizontal(id="settings-buttons"):
                yield Button("Cancel", id="cancel-btn")
                yield Button("Save", id="save-btn", classes="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "save-btn":
            try:
                provider = self.query_one("#provider-select", Select).value
                model = self.query_one("#model-input", Input).value
                max_tokens = int(self.query_one("#max-tokens-input", Input).value)
                temperature = float(self.query_one("#temperature-input", Input).value)
                self.dismiss({
                    "provider": str(provider),
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                })
            except (ValueError, Exception) as e:
                self.app.notify(f"Invalid settings: {e}", severity="error")
