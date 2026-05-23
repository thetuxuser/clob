"""Orchestrator agent — coordinates tasks between multiple agents."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from . import BaseAgent
from .coder import CoderAgent

if TYPE_CHECKING:
    from ..core.runtime import Runtime


class Orchestrator(BaseAgent):
    """
    Supervisor agent that coordinates work between specialized agents.
    """

    name = "orchestrator"

    SYSTEM_PROMPT = """You are an AI orchestrator.
Your job is to break down complex tasks and delegate them to specialized agents.

Available agents:
- coder: Expert software engineer for writing and editing code.

To delegate a task, use the following format:
[DELEGATE: <agent_name>] <task_description>
"""

    def __init__(self, runtime: Runtime) -> None:
        super().__init__(runtime)
        self._agents: dict[str, type[BaseAgent]] = {
            "coder": CoderAgent,
        }

    def get_agent(self, name: str) -> BaseAgent | None:
        agent_cls = self._agents.get(name)
        if agent_cls:
            return agent_cls(self.runtime)
        return None

    async def run(self, task: str, **kwargs: Any) -> AsyncIterator[str]:
        from ..providers.base import ChatMessage

        provider = self.runtime.registry.get(self.runtime.provider)
        if not provider:
            yield "No provider configured."
            return

        messages = [
            ChatMessage(role="system", content=self.SYSTEM_PROMPT),
            ChatMessage(role="user", content=task),
        ]

        full_response = ""
        async for chunk in provider.stream_chat(messages, model=self.runtime.model, **kwargs):
            if chunk.delta:
                full_response += chunk.delta
                yield chunk.delta

        # Simple delegation logic: check for [DELEGATE: agent] in response
        if "[DELEGATE:" in full_response:
            import re

            match = re.search(r"\[DELEGATE:\s*(\w+)\]\s*(.*)", full_response, re.DOTALL)
            if match:
                agent_name = match.group(1).lower()
                subtask = match.group(2).strip()

                yield f"\n\n--- Delegating to {agent_name} ---\n"
                async for subchunk in self.execute_agent(agent_name, subtask, **kwargs):
                    yield subchunk
