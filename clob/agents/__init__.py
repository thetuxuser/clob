"""Agent foundations for clob."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from ..providers.base import ChatMessage as ChatMessage


class BaseAgent:
    """Base class for all agents."""

    name: str = "base"

    def __init__(self, runtime) -> None:
        self.runtime = runtime

    async def run(self, task: str, **kwargs: Any) -> AsyncIterator[str]:
        raise NotImplementedError
