"""NVIDIA Build provider."""

from __future__ import annotations

from ..config.settings import ProviderConfig
from .openai_compatible import OpenAICompatibleProvider


class NvidiaBuildProvider(OpenAICompatibleProvider):
    """NVIDIA Build — access NVIDIA-hosted models."""

    name = "nvidia"

    def __init__(self, config: ProviderConfig) -> None:
        config.base_url = config.base_url or "https://integrate.api.nvidia.com/v1"
        super().__init__(config)
