"""Anthropic Claude provider — native Messages API support."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from ..config.settings import ProviderConfig
from .base import BaseProvider, ChatChunk, ChatMessage, ModelInfo


class AnthropicProvider(BaseProvider):
    """
    Anthropic provider using their native Messages API.
    """

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.name = "anthropic"
        self._client: httpx.AsyncClient | None = None
        self.base_url = config.base_url or "https://api.anthropic.com/v1"

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
                **self.config.extra_headers,
            }
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.config.timeout,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def list_models(self) -> list[ModelInfo]:
        # Anthropic doesn't have a public models endpoint that is easy to use like OpenAI's
        # Returning common ones or empty list if they decide to add one.
        return [
            ModelInfo(id="claude-3-5-sonnet-20241022", name="Claude 3.5 Sonnet", provider="anthropic"),
            ModelInfo(id="claude-3-opus-20240229", name="Claude 3 Opus", provider="anthropic"),
            ModelInfo(id="claude-3-sonnet-20240229", name="Claude 3 Sonnet", provider="anthropic"),
            ModelInfo(id="claude-3-haiku-20240307", name="Claude 3 Haiku", provider="anthropic"),
        ]

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        **kwargs: Any,
    ) -> str:
        client = self._get_client()
        system_prompt = ""
        anthropic_messages = []

        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                anthropic_messages.append({"role": m.role, "content": m.content})

        payload = {
            "model": model,
            "messages": anthropic_messages,
            "stream": False,
            "max_tokens": kwargs.get("max_tokens", 4096),
            **{k: v for k, v in kwargs.items() if k not in ["max_tokens", "stream"]},
        }
        if system_prompt:
            payload["system"] = system_prompt

        resp = await client.post("/messages", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[ChatChunk]:
        client = self._get_client()
        system_prompt = ""
        anthropic_messages = []

        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                anthropic_messages.append({"role": m.role, "content": m.content})

        payload = {
            "model": model,
            "messages": anthropic_messages,
            "stream": True,
            "max_tokens": kwargs.get("max_tokens", 4096),
            **{k: v for k, v in kwargs.items() if k not in ["max_tokens", "stream"]},
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with client.stream("POST", "/messages", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                raw = line[6:]
                try:
                    event = json.loads(raw)
                    event_type = event.get("type")

                    if event_type == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield ChatChunk(
                                delta=delta.get("text", ""),
                                model=model,
                            )
                    elif event_type == "message_stop":
                        yield ChatChunk(finish_reason="end_turn", model=model)
                        break
                except (json.JSONDecodeError, KeyError):
                    continue
