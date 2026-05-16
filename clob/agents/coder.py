"""Coding agent — specialized for code generation and editing."""

from __future__ import annotations

from typing import Any, AsyncIterator

from . import BaseAgent


class CoderAgent(BaseAgent):
    """Agent specialized for code generation and editing tasks."""

    name = "coder"

    SYSTEM_PROMPT = """You are an expert software engineer.
When asked to write code:
1. Always wrap code in markdown fences with the language tag
2. Explain what the code does
3. Mention any dependencies
4. Follow best practices for the language
"""

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
        async for chunk in provider.stream_chat(messages, model=self.runtime.model, **kwargs):
            if chunk.delta:
                yield chunk.delta
