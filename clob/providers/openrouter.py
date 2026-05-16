"""OpenRouter provider — access hundreds of models via one API."""

from __future__ import annotations

from ..config.settings import ProviderConfig
from .openai_compatible import OpenAICompatibleProvider


class OpenRouterProvider(OpenAICompatibleProvider):
    """OpenRouter provider with extra headers for app identification."""

    name = "openrouter"

    def __init__(self, config: ProviderConfig) -> None:
        config.base_url = config.base_url or "https://openrouter.ai/api/v1"
        config.extra_headers.setdefault("HTTP-Referer", "https://github.com/crishacks/clob")
        config.extra_headers.setdefault("X-Title", "clob")
        super().__init__(config)
