"""clob TUI v0.2.0 — modernized terminal AI workspace."""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)

from ..config.settings import AppConfig
from ..core.runtime import Runtime
from ..memory.models import Session
from .screens.memory_search import MemorySearchScreen
from .screens.palette import CommandPalette
from .screens.settings import SettingsScreen
from .screens.usage import UsageScreen
from .widgets import MessageWidget, StatusBar, StreamingMarkdownWidget

CSS_PATH = Path(__file__).parent / "themes" / "dark.tcss"


class SessionItem(ListItem):
    def __init__(self, session: Session, **kwargs) -> None:
        super().__init__(**kwargs)
        self.session = session

    def compose(self) -> ComposeResult:
        title = (
            self.session.title[:22] + "…" if len(self.session.title) > 23 else self.session.title
        )
        yield Label(f"💬 {title}")


class ClobApp(App):
    """clob v0.2.0 — Universal AI terminal platform."""

    CSS_PATH = str(CSS_PATH)
    TITLE = "clob"
    SUB_TITLE = "Universal AI in your terminal"

    BINDINGS = [
        Binding("ctrl+p", "command_palette", "Commands"),
        Binding("ctrl+n", "new_session", "New Chat"),
        Binding("ctrl+s", "action_settings", "Settings"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+l", "clear_chat", "Clear"),
        Binding("ctrl+u", "show_usage", "Usage"),
        Binding("ctrl+f", "search_memory", "Search"),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar"),
        Binding("escape", "focus_input", "Focus Input"),
    ]

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.runtime = Runtime(config)
        self._sessions: list[Session] = []
        self._is_streaming = False
        self._sidebar_visible = True

    # ── Compose ────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="app-layout"):
            with Vertical(id="sidebar"):
                yield Label(" clob", id="sidebar-title")
                yield ListView(id="session-list")
                yield Button("＋ New Chat", id="new-session-btn", classes="primary")

            with Vertical(id="main-area"):
                with Horizontal(id="header"):
                    yield Label("", id="provider-label")
                    yield Label(" › ", id="sep-label")
                    yield Label("", id="model-label")
                    yield Label("", id="caps-label")

                with ScrollableContainer(id="chat-scroll"):
                    yield Vertical(id="chat-container")

                with Horizontal(id="input-area"):
                    yield Input(
                        placeholder="Message… (Enter send, @file inject context, Ctrl+P commands)",
                        id="prompt-input",
                    )

        yield StatusBar(id="status-bar")
        yield Footer()

    # ── Startup ────────────────────────────────────────────────

    async def on_mount(self) -> None:
        await self.runtime.start()
        await self._refresh_sessions()
        self._update_header()
        self.query_one("#prompt-input", Input).focus()
        if not self._sessions:
            await self._show_welcome()

    async def _show_welcome(self) -> None:
        container = self.query_one("#chat-container", Vertical)
        caps = self.runtime.capabilities
        badge_str = "  ".join(caps.badge_list()) or "chat streaming"
        await container.mount(
            Static(
                f"\n[bold #58a6ff]clob v0.2.0[/bold #58a6ff] — Universal AI in your terminal\n\n"
                f"[dim]Provider:[/dim] [green]{self.runtime.provider}[/green]  "
                f"[dim]Model:[/dim] {self.runtime.model}\n"
                f"[dim]Capabilities:[/dim] {badge_str}\n\n"
                f"[dim]Tips:\n"
                f"  @file path.py   → inject file context\n"
                f"  @dir src/       → inject directory\n"
                f"  @workspace      → inject workspace overview\n"
                f"  Ctrl+P          → command palette\n"
                f"  Ctrl+U          → usage report[/dim]\n",
                id="welcome-msg",
            )
        )

    # ── Header ─────────────────────────────────────────────────

    def _update_header(self) -> None:
        try:
            caps = self.runtime.capabilities
            self.query_one("#provider-label", Label).update(
                f"[bold green]{self.runtime.provider}[/bold green]"
            )
            self.query_one("#model-label", Label).update(f"[dim]{self.runtime.model}[/dim]")
            badge_str = "  ".join(caps.badge_list()[:3])
            self.query_one("#caps-label", Label).update(
                f"  [dim cyan]{badge_str}[/dim cyan]" if badge_str else ""
            )
            status = "streaming" if self._is_streaming else "ready"
            self.query_one("#status-bar", StatusBar).update_info(
                provider=self.runtime.provider,
                model=self.runtime.model,
                status=status,
                stats=self.runtime.session_stats_line(),
                capabilities=caps.badge_list(),
            )
        except Exception:
            pass

    # ── Sessions ───────────────────────────────────────────────

    async def _refresh_sessions(self) -> None:
        self._sessions = await self.runtime.memory.get_sessions(limit=30)
        lv = self.query_one("#session-list", ListView)
        lv.clear()
        for s in self._sessions:
            lv.append(SessionItem(s))

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        if not isinstance(event.item, SessionItem):
            return
        await self.runtime.load_session(event.item.session.id)
        await self._load_session_messages(event.item.session.id)
        self._update_header()

    async def _load_session_messages(self, session_id: int) -> None:
        messages = await self.runtime.memory.get_history(session_id)
        container = self.query_one("#chat-container", Vertical)
        await container.remove_children()
        for msg in messages:
            await container.mount(MessageWidget(msg.role, msg.content))
        self._scroll_bottom()

    # ── Chat ───────────────────────────────────────────────────

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "prompt-input":
            return
        text = event.value.strip()
        if not text or self._is_streaming:
            return
        event.input.clear()
        await self._send_message(text)

    async def _send_message(self, text: str) -> None:
        container = self.query_one("#chat-container", Vertical)
        try:
            self.query_one("#welcome-msg").remove()
        except Exception:
            pass

        await container.mount(MessageWidget("user", text))

        streaming = StreamingMarkdownWidget()
        await container.mount(streaming)
        self._scroll_bottom()

        self._is_streaming = True
        self._update_header()

        self.run_worker(self._stream_worker(text, streaming), exclusive=False, thread=False)

    async def _stream_worker(self, text: str, widget: StreamingMarkdownWidget) -> None:
        try:
            async for chunk in self.runtime.stream_response(text):
                if chunk.delta:
                    widget.append_token(chunk.delta)
                    self._scroll_bottom()
        except Exception as e:
            widget.append_token(f"\n\n**Error:** {e}")
        finally:
            widget.finalize()
            self._is_streaming = False
            self._update_header()
            await self._refresh_sessions()
            try:
                self.query_one("#prompt-input", Input).focus()
            except Exception:
                pass

    def _scroll_bottom(self) -> None:
        try:
            self.query_one("#chat-scroll", ScrollableContainer).scroll_end(animate=False)
        except Exception:
            pass

    # ── Actions ────────────────────────────────────────────────

    async def action_command_palette(self) -> None:
        def on_command(action: str | None) -> None:
            if action:
                self.call_later(self._dispatch_command, action)

        await self.push_screen(CommandPalette(), on_command)

    async def _dispatch_command(self, action: str) -> None:
        method = getattr(self, f"action_{action}", None)
        if method:
            result = method()
            if asyncio.iscoroutine(result):
                await result
        else:
            self.notify(f"Unknown command: {action}", severity="warning")

    async def action_new_session(self) -> None:
        await self.runtime.new_session()
        container = self.query_one("#chat-container", Vertical)
        await container.remove_children()
        await self._refresh_sessions()
        await self._show_welcome()
        self.query_one("#prompt-input", Input).focus()

    async def action_action_settings(self) -> None:
        def on_close(result: dict | None) -> None:
            if result:
                self.runtime.set_provider(result["provider"])
                self.runtime.set_model(result["model"])
                self.config.default.provider = result["provider"]
                self.config.default.model = result["model"]
                self.config.default.max_tokens = result["max_tokens"]
                self.config.default.temperature = result["temperature"]
                self._update_header()
                self.notify("Settings saved!", severity="information")

        await self.push_screen(SettingsScreen(self.config), on_close)

    async def action_show_usage(self) -> None:
        report = self.runtime.analytics.format_usage_report()
        await self.push_screen(UsageScreen(report))

    async def action_search_memory(self) -> None:
        await self.push_screen(MemorySearchScreen(self.runtime.memory))

    async def action_export_session(self) -> None:
        if not self.runtime._current_session_id:
            self.notify("No active session to export.", severity="warning")
            return
        history = await self.runtime.memory.get_history(self.runtime._current_session_id)
        lines = ["# Session Export\n"]
        for msg in history:
            lines.append(f"**{msg.role.title()}:** {msg.content}\n")
        output_path = Path.cwd() / "clob-session-export.md"
        output_path.write_text("\n".join(lines))
        self.notify(f"Exported to {output_path}", severity="information")

    async def action_switch_provider(self) -> None:
        await self.action_action_settings()

    async def action_switch_model(self) -> None:
        await self.action_action_settings()

    async def action_run_doctor(self) -> None:
        self.notify("Run 'clob doctor' in your terminal for diagnostics.", severity="information")

    def action_clear_chat(self) -> None:
        try:
            container = self.query_one("#chat-container", Vertical)
            self.call_after_refresh(container.remove_children)
        except Exception:
            pass

    def action_focus_input(self) -> None:
        try:
            self.query_one("#prompt-input", Input).focus()
        except Exception:
            pass

    def action_toggle_sidebar(self) -> None:
        try:
            sidebar = self.query_one("#sidebar", Vertical)
            self._sidebar_visible = not self._sidebar_visible
            sidebar.display = self._sidebar_visible
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new-session-btn":
            await self.action_new_session()

    async def on_unmount(self) -> None:
        await self.runtime.stop()
