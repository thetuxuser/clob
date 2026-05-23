"""Configuration models and settings for clob."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

CONFIG_DIR = Path.home() / ".config" / "clob"
CONFIG_FILE = CONFIG_DIR / "config.toml"
DB_FILE = CONFIG_DIR / "clob.db"


class ProviderConfig(BaseModel):
    """Configuration for a single provider."""

    name: str = ""
    base_url: str = ""
    api_key: str = ""
    chat_endpoint: str = "/chat/completions"
    models_endpoint: str = "/models"
    images_endpoint: str = "/images/generations"
    embeddings_endpoint: str = "/embeddings"
    extra_headers: dict[str, str] = Field(default_factory=dict)
    timeout: float = 60.0
    enabled: bool = True

    @field_validator("api_key", mode="before")
    @classmethod
    def resolve_env(cls, v: str) -> str:
        """Resolve env:VAR_NAME references."""
        if isinstance(v, str) and v.startswith("env:"):
            env_var = v[4:]
            return os.environ.get(env_var, "")
        return v or ""


class DefaultConfig(BaseModel):
    """Default provider/model selection."""

    provider: str = "openrouter"
    model: str = "openai/gpt-4o-mini"
    stream: bool = True
    max_tokens: int = 4096
    temperature: float = 0.7
    system_prompt: str = "You are a helpful AI assistant."
    theme: str = "dark"


class AppConfig(BaseModel):
    """Full application configuration."""

    default: DefaultConfig = Field(default_factory=DefaultConfig)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    profiles: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def load(cls) -> AppConfig:
        if not CONFIG_FILE.exists():
            return cls._create_defaults()
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> AppConfig:
        default = DefaultConfig(**data.get("default", {}))
        providers: dict[str, ProviderConfig] = {}
        for name, pdata in data.get("providers", {}).items():
            providers[name] = ProviderConfig(name=name, **pdata)
        profiles = data.get("profiles", {})
        return cls(default=default, providers=providers, profiles=profiles)

    def apply_profile(self, name: str) -> bool:
        p = self.profiles.get(name)
        if not p:
            return False
        if p.get("provider"):
            self.default.provider = p["provider"]
        if p.get("model"):
            self.default.model = p["model"]
        if p.get("system_prompt"):
            self.default.system_prompt = p["system_prompt"]
        if p.get("temperature") is not None:
            self.default.temperature = p["temperature"]
        if p.get("max_tokens") is not None:
            self.default.max_tokens = p["max_tokens"]
        return True

    @classmethod
    def _create_defaults(cls) -> AppConfig:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config = cls()
        config.providers = {
            "openrouter": ProviderConfig(
                name="openrouter",
                base_url="https://openrouter.ai/api/v1",
                api_key="env:OPENROUTER_API_KEY",
            ),
            "groq": ProviderConfig(
                name="groq",
                base_url="https://api.groq.com/openai/v1",
                api_key="env:GROQ_API_KEY",
            ),
            "ollama": ProviderConfig(
                name="ollama",
                base_url="http://localhost:11434",
                api_key="",
                chat_endpoint="/api/chat",
                models_endpoint="/api/tags",
            ),
            "nvidia": ProviderConfig(
                name="nvidia",
                base_url="https://integrate.api.nvidia.com/v1",
                api_key="env:NVIDIA_API_KEY",
            ),
            "anthropic": ProviderConfig(
                name="anthropic",
                base_url="https://api.anthropic.com/v1",
                api_key="env:ANTHROPIC_API_KEY",
            ),
        }
        _write_default_config(config)
        return config

    def get_provider(self, name: str) -> ProviderConfig | None:
        return self.providers.get(name)

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _write_default_config(self)


def _write_default_config(config: AppConfig) -> None:
    """Write a default config.toml."""
    lines = [
        "# clob configuration\n",
        "# https://github.com/crishacks/clob\n\n",
        "[default]\n",
        f'provider = "{config.default.provider}"\n',
        f'model = "{config.default.model}"\n',
        f"stream = {str(config.default.stream).lower()}\n",
        f"max_tokens = {config.default.max_tokens}\n",
        f"temperature = {config.default.temperature}\n",
        f'theme = "{config.default.theme}"\n\n',
    ]
    for pname, pconf in config.providers.items():
        lines.append(f"[providers.{pname}]\n")
        lines.append(f'base_url = "{pconf.base_url}"\n')
        # Don't write resolved keys back — keep env: refs
        lines.append(f'api_key = "env:{pname.upper()}_API_KEY"\n\n')

    with open(CONFIG_FILE, "w") as f:
        f.writelines(lines)


class ProfileConfig(BaseModel):
    """A named configuration profile (work, local, etc.)."""

    provider: str = ""
    model: str = ""
    system_prompt: str = ""
    temperature: float | None = None
    max_tokens: int | None = None
