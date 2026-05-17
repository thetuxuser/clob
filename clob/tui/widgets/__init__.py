"""Upgraded TUI widgets for clob v0.2.0."""

from __future__ import annotations

from rich.markdown import Markdown
from rich.text import Text
from textual.reactive import reactive
from textual.widgets import Static


class MessageWidget(Static):
    """Renders a single chat message with rich markdown."""

    DEFAULT_CSS = """
    MessageWidget { height: auto; margin: 0 0 1 0; }
    """

    def __init__(self, role: str, content: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.role = role
        self.content = content

    def render(self):
        if self.role == "user":
            return Text.from_markup(f"[bold blue]▶ You[/bold blue]\n{self.content}")
        elif self.role == "assistant":
            try:
                return Markdown(f"**◆ AI**\n\n{self.content}")
            except Exception:
                return Text(f"◆ AI\n{self.content}")
        return Text(f"{self.role}\n{self.content}")


class StreamingMarkdownWidget(Static):
    """Live streaming markdown widget with code-fence awareness."""

    DEFAULT_CSS = """
    StreamingMarkdownWidget {
        height: auto; margin: 0 0 1 0;
        border-left: solid #3fb950; padding-left: 1;
    }
    """
    _revision: reactive[int] = reactive(0, layout=True)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._raw = ""
        self._in_fence = False
        self._complete = False
        self._token_count = 0

    def append_token(self, token: str) -> None:
        self._raw += token
        self._token_count += 1
        opens = self._raw.count("```")
        self._in_fence = (opens % 2) == 1
        if self._token_count % 3 == 0 or "\n" in token:
            self._revision += 1

    def finalize(self) -> None:
        self._complete = True
        self._in_fence = False
        self._revision += 1

    def cancel(self) -> None:
        self._raw += "\n\n*[cancelled]*"
        self.finalize()

    @property
    def full_text(self) -> str:
        return self._raw

    @property
    def token_count(self) -> int:
        return self._token_count

    def render(self):
        cursor = "" if self._complete else "▌"
        render_text = self._raw
        if self._in_fence:
            render_text = self._raw + "\n```"
        render_text += cursor
        try:
            return Markdown(f"**◆ AI**\n\n{render_text}")
        except Exception:
            return Text(f"◆ AI\n{render_text}")


class StatusBar(Static):
    """Enhanced status bar with provider, model, stats, streaming state."""

    DEFAULT_CSS = """
    StatusBar { height: 1; background: #161b22; color: #8b949e; padding: 0 1; dock: bottom; }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._provider = ""
        self._model = ""
        self._status = "ready"
        self._stats = ""
        self._capabilities: list[str] = []

    def update_info(
        self,
        provider: str,
        model: str,
        status: str = "ready",
        stats: str = "",
        capabilities: list[str] | None = None,
    ) -> None:
        self._provider = provider
        self._model = model
        self._status = status
        self._stats = stats
        self._capabilities = capabilities or []
        self.refresh()

    def render(self):
        t = Text()
        t.append(" clob v0.2 ", style="bold #58a6ff")
        t.append("│ ", style="dim")
        t.append(self._provider or "—", style="bold green")
        t.append(" › ", style="dim")
        model_display = self._model[:28] + "…" if len(self._model) > 29 else self._model
        t.append(model_display or "—", style="white")
        if self._capabilities:
            t.append("  " + " ".join(self._capabilities[:2]), style="dim cyan")
        if self._stats:
            t.append("  │  " + self._stats, style="dim yellow")
        t.append("  │  ", style="dim")
        if self._status == "streaming":
            t.append("● streaming", style="bold yellow")
        elif self._status == "error":
            t.append("✗ error", style="bold red")
        elif self._status == "indexing":
            t.append("⟳ indexing", style="bold cyan")
        else:
            t.append("● ready", style="green")
        t.append("  ctrl+p commands  ctrl+n new  ctrl+q quit", style="dim")
        return t
