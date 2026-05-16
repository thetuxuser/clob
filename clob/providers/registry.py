"""Provider registry — manages all available providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseProvider
from .groq import GroqProvider
from .nvidia_build import NvidiaBuildProvider
from .ollama import OllamaProvider
from .openai_compatible import OpenAICompatibleProvider
from .openrouter import OpenRouterProvider
from ..config.settings import AppConfig, ProviderConfig

if TYPE_CHECKING:
    pass

# Map provider name → class
_BUILTIN_PROVIDERS: dict[str, type[BaseProvider]] = {
    "openrouter": OpenRouterProvider,
    "groq": GroqProvider,
    "nvidia": NvidiaBuildProvider,
    "ollama": OllamaProvider,
}


class ProviderRegistry:
    """Central registry for provider instances."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def load_from_config(self, config: AppConfig) -> None:
        """Instantiate all enabled providers from config."""
        for name, pconf in config.providers.items():
            if not pconf.enabled:
                continue
            self._providers[name] = self._build(name, pconf)

    def _build(self, name: str, config: ProviderConfig) -> BaseProvider:
        cls = _BUILTIN_PROVIDERS.get(name, OpenAICompatibleProvider)
        return cls(config)

    def get(self, name: str) -> BaseProvider | None:
        return self._providers.get(name)

    def register(self, name: str, provider: BaseProvider) -> None:
        self._providers[name] = provider

    def list_names(self) -> list[str]:
        return list(self._providers.keys())

    def add_custom(self, config: ProviderConfig) -> BaseProvider:
        provider = OpenAICompatibleProvider(config)
        self._providers[config.name] = provider
        return provider

    async def close_all(self) -> None:
        for provider in self._providers.values():
            if hasattr(provider, "close"):
                await provider.close()


# Global registry instance
registry = ProviderRegistry()
