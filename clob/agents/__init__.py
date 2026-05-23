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

    async def execute_agent(self, agent_name: str, task: str, **kwargs: Any) -> AsyncIterator[str]:
        """Delegate a task to another agent."""
        from .orchestrator import Orchestrator

        # Avoid circular imports and infinite recursion
        if agent_name == self.name:
            yield f"Error: Agent '{self.name}' cannot call itself."
            return

        orchestrator = Orchestrator(self.runtime)
        agent = orchestrator.get_agent(agent_name)
        if not agent:
            yield f"Error: Agent '{agent_name}' not found."
            return

        async for chunk in agent.run(task, **kwargs):
            yield chunk
