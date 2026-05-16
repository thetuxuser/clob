"""Abstract base class for all AI providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str  # system | user | assistant
    content: str


class ChatChunk(BaseModel):
    """A streaming chunk from a provider."""

    delta: str = ""
    finish_reason: str | None = None
    model: str = ""


class ModelInfo(BaseModel):
    """Info about an available model."""

    id: str
    name: str = ""
    context_length: int | None = None
    provider: str = ""


class BaseProvider(ABC):
    """Abstract base for all AI providers."""

    name: str = "base"

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List available models."""
        ...

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        **kwargs: Any,
    ) -> str:
        """Send a chat request and return full response."""
        ...

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[ChatMessage],
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[ChatChunk]:
        """Stream chat response chunks."""
        ...

    async def generate_image(self, prompt: str, **kwargs: Any) -> bytes | None:
        """Generate an image. Override in subclasses."""
        raise NotImplementedError(f"{self.name} does not support image generation")

    async def embeddings(self, text: str, model: str = "", **kwargs: Any) -> list[float]:
        """Generate text embeddings. Override in subclasses."""
        raise NotImplementedError(f"{self.name} does not support embeddings")

    async def health_check(self) -> bool:
        """Check if provider is reachable."""
        try:
            await self.list_models()
            return True
        except Exception:
            return False
