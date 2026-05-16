"""Ollama provider — local AI models."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx

from .base import BaseProvider, ChatChunk, ChatMessage, ModelInfo
from ..config.settings import ProviderConfig


class OllamaProvider(BaseProvider):
    """Ollama provider for locally running AI models."""

    name = "ollama"

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.base_url = config.base_url or "http://localhost:11434"
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.config.timeout,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def list_models(self) -> list[ModelInfo]:
        client = self._get_client()
        try:
            resp = await client.get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [
                ModelInfo(
                    id=m["name"],
                    name=m["name"],
                    provider="ollama",
                )
                for m in data.get("models", [])
            ]
        except Exception:
            return []

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        **kwargs: Any,
    ) -> str:
        client = self._get_client()
        payload = {
            "model": model,
            "messages": [m.model_dump() for m in messages],
            "stream": False,
            **kwargs,
        }
        resp = await client.post("/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[ChatChunk]:
        client = self._get_client()
        payload = {
            "model": model,
            "messages": [m.model_dump() for m in messages],
            "stream": True,
            **kwargs,
        }
        async with client.stream("POST", "/api/chat", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    msg = chunk.get("message", {})
                    content = msg.get("content", "")
                    done = chunk.get("done", False)
                    yield ChatChunk(
                        delta=content,
                        finish_reason="stop" if done else None,
                        model=model,
                    )
                    if done:
                        break
                except json.JSONDecodeError:
                    continue

    async def embeddings(self, text: str, model: str = "nomic-embed-text", **kwargs: Any) -> list[float]:
        client = self._get_client()
        resp = await client.post("/api/embeddings", json={"model": model, "prompt": text})
        resp.raise_for_status()
        return resp.json()["embedding"]

    async def pull_model(self, model: str) -> AsyncIterator[str]:
        """Pull a model from Ollama registry."""
        client = self._get_client()
        async with client.stream("POST", "/api/pull", json={"name": model, "stream": True}) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        status = data.get("status", "")
                        yield status
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> bool:
        client = self._get_client()
        try:
            resp = await client.get("/")
            return resp.status_code == 200
        except Exception:
            return False
