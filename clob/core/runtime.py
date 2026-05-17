"""Core runtime v0.2.0 — wires providers, memory, analytics, workspace."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ..analytics import AnalyticsTracker, TurnStats
from ..config.settings import AppConfig
from ..memory.manager import MemoryManager
from ..providers.base import ChatChunk, ChatMessage
from ..providers.capabilities import ProviderCapabilities, get_capabilities
from ..providers.registry import ProviderRegistry
from ..workspace import resolve_context_refs


class Runtime:
    """
    Central runtime v0.2.0:
    - Provider selection + capability awareness
    - Streaming with token counting
    - Analytics tracking
    - Workspace context injection (@file, @dir, @workspace)
    - Session management
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.registry = ProviderRegistry()
        self.memory = MemoryManager()
        self.analytics = AnalyticsTracker()
        self._current_session_id: int | None = None
        self._current_provider: str = config.default.provider
        self._current_model: str = config.default.model
        self._workspace_root: Path = Path.cwd()

    async def start(self) -> None:
        self.registry.load_from_config(self.config)
        await self.memory.start()

    async def stop(self) -> None:
        await self.registry.close_all()
        await self.memory.stop()

    @property
    def provider(self) -> str:
        return self._current_provider

    @property
    def model(self) -> str:
        return self._current_model

    @property
    def capabilities(self) -> ProviderCapabilities:
        return get_capabilities(self._current_provider)

    def set_provider(self, name: str) -> bool:
        if self.registry.get(name):
            self._current_provider = name
            return True
        return False

    def set_model(self, model: str) -> None:
        self._current_model = model

    def set_workspace(self, path: Path) -> None:
        self._workspace_root = path.resolve()

    async def ensure_session(self) -> int:
        if self._current_session_id is None:
            session = await self.memory.new_session(
                provider=self._current_provider,
                model=self._current_model,
            )
            self._current_session_id = session.id
        return self._current_session_id

    async def new_session(self) -> int:
        session = await self.memory.new_session(
            provider=self._current_provider,
            model=self._current_model,
        )
        self._current_session_id = session.id
        return session.id

    async def load_session(self, session_id: int) -> bool:
        session = await self.memory.get_session(session_id)
        if session:
            self._current_session_id = session_id
            if session.provider:
                self._current_provider = session.provider
            if session.model:
                self._current_model = session.model
            return True
        return False

    async def _resolve_input(self, user_input: str) -> str:
        if any(ref in user_input for ref in ("@file", "@dir", "@workspace")):
            return resolve_context_refs(user_input, self._workspace_root)
        return user_input

    async def _build_messages(self, session_id: int) -> list[ChatMessage]:
        messages: list[ChatMessage] = []
        system = self.config.default.system_prompt
        if system:
            messages.append(ChatMessage(role="system", content=system))
        history = await self.memory.get_history(session_id)
        for msg in history:
            messages.append(ChatMessage(role=msg.role, content=msg.content))
        return messages

    async def stream_response(self, user_input: str, **kwargs: Any) -> AsyncIterator[ChatChunk]:
        provider = self.registry.get(self._current_provider)
        if not provider:
            raise RuntimeError(
                f"Provider '{self._current_provider}' not configured. "
                "Run 'clob doctor' to check setup."
            )

        await self._resolve_input(user_input)
        session_id = await self.ensure_session()
        await self.memory.add_message(session_id, "user", user_input)

        messages = await self._build_messages(session_id)

        t0 = time.monotonic()
        full_response = ""
        input_tokens = sum(len(m.content.split()) for m in messages)

        async for chunk in provider.stream_chat(
            messages,
            model=self._current_model,
            max_tokens=self.config.default.max_tokens,
            temperature=self.config.default.temperature,
            **kwargs,
        ):
            full_response += chunk.delta
            yield chunk

        latency_ms = (time.monotonic() - t0) * 1000
        output_tokens = len(full_response.split())

        await self.memory.add_message(session_id, "assistant", full_response)

        self.analytics.record(
            session_id,
            TurnStats(
                provider=self._current_provider,
                model=self._current_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
            ),
        )

        history = await self.memory.get_history(session_id)
        if len(history) == 2:
            title = user_input[:50].strip()
            await self.memory.rename_session(session_id, title)

    async def chat(self, user_input: str, **kwargs: Any) -> str:
        result = ""
        async for chunk in self.stream_response(user_input, **kwargs):
            result += chunk.delta
        return result

    def session_stats_line(self) -> str:
        if self._current_session_id is None:
            return ""
        stats = self.analytics.get_session(self._current_session_id)
        return stats.summary_line() if stats else ""
