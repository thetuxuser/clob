"""Groq provider — ultra-fast inference."""

from __future__ import annotations

from ..config.settings import ProviderConfig
from .openai_compatible import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    """Groq provider using their OpenAI-compatible API."""

    name = "groq"

    def __init__(self, config: ProviderConfig) -> None:
        config.base_url = config.base_url or "https://api.groq.com/openai/v1"
        super().__init__(config)
