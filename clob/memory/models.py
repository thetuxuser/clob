"""SQLite-backed memory models for sessions and messages."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class Session:
    """A conversation session."""

    def __init__(
        self,
        id: int | None,
        title: str,
        provider: str,
        model: str,
        created_at: datetime,
        updated_at: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.id = id
        self.title = title
        self.provider = provider
        self.model = model
        self.created_at = created_at
        self.updated_at = updated_at
        self.metadata = metadata or {}


class Message:
    """A single message in a session."""

    def __init__(
        self,
        id: int | None,
        session_id: int,
        role: str,
        content: str,
        created_at: datetime,
        tokens: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.id = id
        self.session_id = session_id
        self.role = role
        self.content = content
        self.created_at = created_at
        self.tokens = tokens
        self.metadata = metadata or {}
