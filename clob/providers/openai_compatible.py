"""Generic OpenAI-compatible provider implementation."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from ..config.settings import ProviderConfig
from .base import BaseProvider, ChatChunk, ChatMessage, ModelInfo


class OpenAICompatibleProvider(BaseProvider):
    """
    Universal provider for any OpenAI-compatible API.

    Works automatically with:
    - OpenRouter
    - Groq
    - NVIDIA Build
    - Together AI
    - Anyscale
    - Custom endpoints
    - Any OpenAI-compatible service
    """

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.name = config.name
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {
                "Content-Type": "application/json",
                **self.config.extra_headers,
            }
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=headers,
                timeout=self.config.timeout,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def list_models(self) -> list[ModelInfo]:
        client = self._get_client()
        try:
            resp = await client.get(self.config.models_endpoint)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("data", [])
            return [
                ModelInfo(
                    id=m.get("id", ""),
                    name=m.get("name", m.get("id", "")),
                    context_length=m.get("context_length"),
                    provider=self.name,
                )
                for m in models
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
        resp = await client.post(self.config.chat_endpoint, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

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
        async with client.stream("POST", self.config.chat_endpoint, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                raw = line[6:]
                if raw == "[DONE]":
                    break
                try:
                    chunk = json.loads(raw)
                    choice = chunk["choices"][0]
                    delta = choice.get("delta", {})
                    content = delta.get("content", "")
                    finish = choice.get("finish_reason")
                    yield ChatChunk(
                        delta=content or "",
                        finish_reason=finish,
                        model=chunk.get("model", model),
                    )
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    async def generate_image(self, prompt: str, **kwargs: Any) -> bytes | None:
        client = self._get_client()
        payload = {"prompt": prompt, "n": 1, "size": "1024x1024", **kwargs}
        resp = await client.post(self.config.images_endpoint, json=payload)
        resp.raise_for_status()
        data = resp.json()
        url = data["data"][0].get("url")
        if url:
            img_resp = await client.get(url)
            return img_resp.content
        return None

    async def embeddings(self, text: str, model: str = "", **kwargs: Any) -> list[float]:
        client = self._get_client()
        payload = {"input": text, "model": model, **kwargs}
        resp = await client.post(self.config.embeddings_endpoint, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["embedding"]
