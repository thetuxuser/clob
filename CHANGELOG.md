# Changelog

All notable changes to clob are documented here.

This project adheres to [Semantic Versioning](https://semver.org/) and [Conventional Commits](https://www.conventionalcommits.org/).

---

## [Unreleased]

### Planned
- Voice input support
- VS Code extension
- Web UI companion

---

## [0.3.0] — 2026-05-23

### Added
- **Anthropic Claude native provider** — native `/messages` API support with streaming and vision
- **MCP (Model Context Protocol) support** — foundation for connecting to external MCP servers and tools
- **Multi-agent workflows** — Orchestrator agent capable of delegating tasks to specialized agents

---

## [0.2.0] — 2026-05-16

### Added

#### Core
- **Provider capability system** — `ProviderCapabilities` dataclass with per-provider feature flags (vision, tools, embeddings, json_mode, image generation, audio, streaming)
- **Analytics tracker** — per-session token counting, estimated cost by provider/model, usage reports
- **Workspace context** — `@file path.py`, `@dir src/`, `@workspace` reference injection into AI prompts
- **Workspace indexer** — full project file indexer with language breakdown, token budgeting, `.clobignore` support
- **Config profiles** — named profiles (`[profiles.work]`, `[profiles.local]`) for quick provider/model switching

#### TUI
- **Command palette** — `Ctrl+P` fuzzy command launcher with all app actions
- **Usage analytics screen** — `Ctrl+U` shows token/cost report
- **Memory search screen** — `Ctrl+F` searches conversation history
- **Session export** — export current session as Markdown
- **Sidebar toggle** — `Ctrl+B` shows/hides sidebar
- **Capability badges** — provider capabilities shown in TUI header
- **Live stats in status bar** — token counts and estimated cost update as you chat
- **Improved streaming renderer** — code-fence detection, throttled re-renders, cancel support, reduced flicker

#### Rendering
- **Terminal image renderer** — auto-detects Kitty / iTerm2 / Sixel / ASCII fallback
- **`ImageRenderer` class** — protocol-aware rendering with graceful degradation

#### Security & Execution
- **Sandbox system** — `SAFE / RESTRICTED / FULL` permission levels with execution log
- **Restricted allowlists** — safe commands only by default

#### Themes
- **Theme system** — 4 built-in themes: dark, light, cyberpunk, nord
- **User themes** — place `.tcss` files in `~/.config/clob/themes/`
- `clob theme list` and `clob theme set <name>` CLI commands

#### Attachments
- **Multimodal attachments** — image, text, code, PDF loading with OpenAI content-part format
- Attachment preview in TUI

#### CLI
- `clob workspace index` / `stats` / `context`
- `clob session export` / `delete`
- `clob plugins list` / `install`
- `clob theme list` / `set`
- `clob usage`

### Changed
- Runtime upgraded with analytics, workspace context injection, and capability awareness
- Status bar now shows token stats and capability badges
- Welcome screen shows provider capabilities on startup
- All repo references updated to `crishacks/clob`

### Fixed
- Code fence detection during streaming (no more broken partial fences)
- Streaming widget render throttled to reduce flicker
- Config `_from_dict` now correctly parses profiles block

---

## [0.1.0] — 2026-05-15

### Added

#### Core
- **Textual TUI** — full terminal user interface with sidebar, chat window, streaming output
- **Runtime** — central async runtime wiring providers, memory, and streaming
- **Streaming** — token-by-token async streaming with `async for chunk in provider.stream_chat(...)`

#### Providers
- **OpenRouter** — access to hundreds of models via one API
- **Groq** — ultra-fast inference
- **NVIDIA Build** — NVIDIA-hosted models
- **Ollama** — local model support with model pulling
- **Generic OpenAI-compatible** — any OpenAI-compatible endpoint via config

#### Provider System
- `BaseProvider` abstract class with `chat`, `stream_chat`, `list_models`, `generate_image`, `embeddings`
- `ProviderRegistry` — central provider management
- Custom provider config via `[providers.my-provider]` in `config.toml`

#### Memory
- **SQLite persistence** — sessions, messages, search via `aiosqlite`
- `sessions`, `messages`, `memories` database tables
- Full-text message search

#### CLI
- `clob` — launch TUI
- `clob chat` — single message non-TUI mode
- `clob models` — list available models
- `clob providers` — list configured providers
- `clob config` — show/edit configuration
- `clob memory` — search history, list sessions
- `clob ollama` — list and pull local models
- `clob doctor` — installation diagnostics

#### Configuration
- `~/.config/clob/config.toml` — TOML configuration
- Environment variable resolution (`env:VAR_NAME`)
- Auto-generated default config on first run

#### Developer
- Full `pyproject.toml` with hatchling build
- Ruff + Black code quality tooling
- pytest + pytest-asyncio test suite (11 tests)
- MIT License
- Dockerfile + docker-compose.yml
- GitHub Actions CI (Linux, macOS, Windows) and Release workflows
- Plugin loader system

---

## Version History

| Version | Date | Highlights |
|---------|------|-----------|
| 0.3.0 | 2026-05-23 | Anthropic Claude, MCP support, multi-agent workflows |
| 0.2.0 | 2026-05-16 | Analytics, workspace context, command palette, themes, sandbox |
| 0.1.0 | 2026-05-15 | Initial release — TUI, streaming, 5 providers, SQLite memory |

---

[Unreleased]: https://github.com/crishacks/clob/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/crishacks/clob/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/crishacks/clob/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/crishacks/clob/releases/tag/v0.1.0
