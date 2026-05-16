"""Provider capability detection and registration."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProviderCapabilities:
    """Structured capability flags for a provider."""

    chat: bool = True
    streaming: bool = True
    vision: bool = False
    image_generation: bool = False
    embeddings: bool = False
    audio: bool = False
    video: bool = False
    tool_calling: bool = False
    json_mode: bool = False
    system_prompt: bool = True
    max_context: int = 8192

    def supports(self, feature: str) -> bool:
        return getattr(self, feature, False)

    def badge_list(self) -> list[str]:
        """Return list of capability badge strings for display."""
        badges = []
        if self.vision:
            badges.append("👁 vision")
        if self.image_generation:
            badges.append("🎨 img-gen")
        if self.embeddings:
            badges.append("📐 embed")
        if self.tool_calling:
            badges.append("🔧 tools")
        if self.audio:
            badges.append("🔊 audio")
        if self.json_mode:
            badges.append("{ } json")
        return badges


# ── Known capability profiles ──────────────────────────────────

CAPABILITIES: dict[str, ProviderCapabilities] = {
    "openrouter": ProviderCapabilities(
        chat=True,
        streaming=True,
        vision=True,        # depends on chosen model, but many support it
        image_generation=False,
        embeddings=False,
        tool_calling=True,
        json_mode=True,
        max_context=128000,
    ),
    "groq": ProviderCapabilities(
        chat=True,
        streaming=True,
        vision=True,
        tool_calling=True,
        json_mode=True,
        max_context=32768,
    ),
    "nvidia": ProviderCapabilities(
        chat=True,
        streaming=True,
        vision=True,
        image_generation=True,
        embeddings=True,
        tool_calling=True,
        json_mode=True,
        max_context=128000,
    ),
    "ollama": ProviderCapabilities(
        chat=True,
        streaming=True,
        vision=True,
        embeddings=True,
        tool_calling=False,
        json_mode=True,
        max_context=32768,
    ),
    # Default for unknown providers
    "default": ProviderCapabilities(),
}


def get_capabilities(provider_name: str) -> ProviderCapabilities:
    return CAPABILITIES.get(provider_name, CAPABILITIES["default"])
