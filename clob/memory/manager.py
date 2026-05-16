"""Memory manager — central interface for session/message management."""

from __future__ import annotations

from pathlib import Path

from .models import Message, Session
from .persistence import Database
from ..config.settings import DB_FILE


class MemoryManager:
    """High-level memory management interface."""

    def __init__(self, db_path: Path = DB_FILE) -> None:
        self.db = Database(db_path)

    async def start(self) -> None:
        await self.db.connect()

    async def stop(self) -> None:
        await self.db.close()

    # ── Sessions ──────────────────────────────────────────────────────────

    async def new_session(self, provider: str = "", model: str = "") -> Session:
        return await self.db.create_session(provider=provider, model=model)

    async def get_sessions(self, limit: int = 50) -> list[Session]:
        return await self.db.get_sessions(limit)

    async def get_session(self, session_id: int) -> Session | None:
        return await self.db.get_session(session_id)

    async def rename_session(self, session_id: int, title: str) -> None:
        await self.db.update_session_title(session_id, title)

    async def delete_session(self, session_id: int) -> None:
        await self.db.delete_session(session_id)

    # ── Messages ──────────────────────────────────────────────────────────

    async def add_message(self, session_id: int, role: str, content: str) -> Message:
        return await self.db.add_message(session_id, role, content)

    async def get_history(self, session_id: int) -> list[Message]:
        return await self.db.get_messages(session_id)

    async def search(self, query: str) -> list[Message]:
        return await self.db.search_messages(query)
