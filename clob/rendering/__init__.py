"""Advanced incremental streaming markdown renderer for Textual TUI.

Handles live rendering of partial markdown with:
- Incremental updates
- Code fence detection during stream
- Syntax-highlighted code blocks
- Reduced flickering via buffered updates
- Clean cursor handling
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import ClassVar

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
from textual.widget import Widget
from textual.reactive import reactive
from textual.app import RenderResult


_FENCE_RE = re.compile(r"^```(\w*)", re.MULTILINE)
_FENCE_END_RE = re.compile(r"^```\s*$", re.MULTILINE)


@dataclass
class StreamBuffer:
    """Tracks streaming state for incremental rendering."""

    raw: str = ""
    in_code_fence: bool = False
    fence_lang: str = ""
    fence_start: int = -1
    complete: bool = False
    token_count: int = 0

    def append(self, token: str) -> None:
        self.raw += token
        self.token_count += 1
        self._update_fence_state(token)

    def _update_fence_state(self, token: str) -> None:
        # Detect opening fence
        if not self.in_code_fence:
            m = _FENCE_RE.search(self.raw)
            if m:
                end_fence = _FENCE_END_RE.search(self.raw, m.end())
                if not end_fence:
                    self.in_code_fence = True
                    self.fence_lang = m.group(1) or "text"
                    self.fence_start = m.start()
        else:
            # Detect closing fence
            if _FENCE_END_RE.search(self.raw):
                self.in_code_fence = False

    def render_rich(self) -> Markdown | Text:
        """Render current buffer as Rich renderable."""
        text = self.raw
        cursor = "▌" if not self.complete else ""

        if not text and not cursor:
            return Text("")

        # If we're inside an open code fence, append a closing fence for rendering
        render_text = text
        if self.in_code_fence:
            render_text = text + f"\n```"

        render_text += cursor

        try:
            return Markdown(render_text)
        except Exception:
            return Text(render_text)

    def finalize(self) -> None:
        self.complete = True
        self.in_code_fence = False


class StreamingMarkdownWidget(Widget):
    """
    A Textual widget that live-renders streaming markdown.

    Features:
    - Incremental token appending
    - Rich markdown rendering with syntax highlights
    - Code fence awareness (no broken partial fences)
    - Smooth updates via reactive
    - Cancel support
    """

    DEFAULT_CSS = """
    StreamingMarkdownWidget {
        height: auto;
        padding: 0 1;
        background: transparent;
    }
    """

    _revision: reactive[int] = reactive(0, layout=True)

    def __init__(self, role: str = "assistant", **kwargs) -> None:
        super().__init__(**kwargs)
        self.role = role
        self._buffer = StreamBuffer()

    def append_token(self, token: str) -> None:
        """Append a streaming token and trigger a re-render."""
        self._buffer.append(token)
        self._revision += 1

    def finalize(self) -> None:
        """Mark stream as complete (removes cursor)."""
        self._buffer.finalize()
        self._revision += 1

    def cancel(self) -> None:
        """Cancel mid-stream cleanly."""
        self._buffer.raw += "\n\n*[cancelled]*"
        self.finalize()

    @property
    def full_text(self) -> str:
        return self._buffer.raw

    @property
    def token_count(self) -> int:
        return self._buffer.token_count

    def render(self) -> RenderResult:
        return self._buffer.render_rich()


class MessageRenderer:
    """
    Static helper that renders a complete message to a Rich renderable.
    Used for re-rendering saved messages from history.
    """

    @staticmethod
    def render(role: str, content: str) -> Markdown | Text:
        if role == "assistant":
            try:
                return Markdown(content)
            except Exception:
                return Text(content)
        else:
            return Text(content)
