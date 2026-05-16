"""Agent foundations for clob."""

from __future__ import annotations

from typing import Any, AsyncIterator

from ..providers.base import ChatMessage


class BaseAgent:
    """Base class for all agents."""

    name: str = "base"

    def __init__(self, runtime) -> None:
        self.runtime = runtime

    async def run(self, task: str, **kwargs: Any) -> AsyncIterator[str]:
        raise NotImplementedError
