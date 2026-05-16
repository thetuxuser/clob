"""SQLite persistence layer using aiosqlite."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from .models import Message, Session


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL DEFAULT 'New Chat',
    provider TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    tokens INTEGER NOT NULL DEFAULT 0,
    metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC);
"""


class Database:
    """Async SQLite database wrapper."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(str(self.path))
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    @property
    def db(self) -> aiosqlite.Connection:
        if not self._db:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db

    # ── Sessions ──────────────────────────────────────────────────────────

    async def create_session(
        self, title: str = "New Chat", provider: str = "", model: str = ""
    ) -> Session:
        now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        cur = await self.db.execute(
            "INSERT INTO sessions (title, provider, model, created_at, updated_at, metadata) VALUES (?,?,?,?,?,?)",
            (title, provider, model, now, now, "{}"),
        )
        await self.db.commit()
        return Session(
            id=cur.lastrowid,
            title=title,
            provider=provider,
            model=model,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )

    async def get_sessions(self, limit: int = 50) -> list[Session]:
        cur = await self.db.execute(
            "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?", (limit,)
        )
        rows = await cur.fetchall()
        return [_row_to_session(r) for r in rows]

    async def get_session(self, session_id: int) -> Session | None:
        cur = await self.db.execute("SELECT * FROM sessions WHERE id=?", (session_id,))
        row = await cur.fetchone()
        return _row_to_session(row) if row else None

    async def update_session_title(self, session_id: int, title: str) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        await self.db.execute(
            "UPDATE sessions SET title=?, updated_at=? WHERE id=?", (title, now, session_id)
        )
        await self.db.commit()

    async def delete_session(self, session_id: int) -> None:
        await self.db.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        await self.db.commit()

    # ── Messages ──────────────────────────────────────────────────────────

    async def add_message(
        self, session_id: int, role: str, content: str, tokens: int = 0
    ) -> Message:
        now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        cur = await self.db.execute(
            "INSERT INTO messages (session_id, role, content, created_at, tokens, metadata) VALUES (?,?,?,?,?,?)",
            (session_id, role, content, now, tokens, "{}"),
        )
        # touch session updated_at
        await self.db.execute(
            "UPDATE sessions SET updated_at=? WHERE id=?", (now, session_id)
        )
        await self.db.commit()
        return Message(
            id=cur.lastrowid,
            session_id=session_id,
            role=role,
            content=content,
            created_at=datetime.fromisoformat(now),
            tokens=tokens,
        )

    async def get_messages(self, session_id: int) -> list[Message]:
        cur = await self.db.execute(
            "SELECT * FROM messages WHERE session_id=? ORDER BY created_at ASC",
            (session_id,),
        )
        rows = await cur.fetchall()
        return [_row_to_message(r) for r in rows]

    async def search_messages(self, query: str, limit: int = 20) -> list[Message]:
        cur = await self.db.execute(
            "SELECT * FROM messages WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{query}%", limit),
        )
        rows = await cur.fetchall()
        return [_row_to_message(r) for r in rows]


def _row_to_session(row: aiosqlite.Row) -> Session:
    return Session(
        id=row["id"],
        title=row["title"],
        provider=row["provider"],
        model=row["model"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        metadata=json.loads(row["metadata"]),
    )


def _row_to_message(row: aiosqlite.Row) -> Message:
    return Message(
        id=row["id"],
        session_id=row["session_id"],
        role=row["role"],
        content=row["content"],
        created_at=datetime.fromisoformat(row["created_at"]),
        tokens=row["tokens"],
        metadata=json.loads(row["metadata"]),
    )
