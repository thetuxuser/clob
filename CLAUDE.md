# CLAUDE.md — AI Assistant Context for clob

This file provides context for AI coding assistants (Claude, Copilot, Cursor, etc.) working on the clob codebase.

---

## Project Overview

**clob** is an open-source universal AI terminal platform written in Python.

- **Repo:** [github.com/crishacks/clob](https://github.com/crishacks/clob)
- **Version:** 0.3.0
- **License:** MIT
- **Python:** 3.12+

---

## Architecture Summary

```
clob/
├── tui/           # Textual TUI — ClobApp, screens, widgets
├── core/          # Runtime — central async orchestrator
├── providers/     # AI providers — base, openrouter, groq, nvidia, ollama, openai_compatible
├── memory/        # SQLite persistence — sessions, messages, search
├── analytics/     # Token counting + cost estimation
├── workspace/     # @file @dir @workspace context injection
├── indexing/      # File indexer with language detection
├── rendering/     # Streaming markdown + terminal image rendering
├── sandbox/       # Safe shell execution with permission levels
├── themes/        # TCSS theme system
├── attachments/   # Multimodal file handling
├── plugins/       # Dynamic plugin loading
├── agents/        # AI agent foundations
├── tools/         # Shell, filesystem, git tools
├── config/        # Settings, profiles, TOML loader
└── main.py        # Typer CLI entry point
```

---

## Key Design Decisions

### Provider abstraction
All providers implement `BaseProvider` from `clob/providers/base.py`. The `OpenAICompatibleProvider` handles any OpenAI-compatible API — adding a new provider usually means subclassing it with a custom base URL.

### Async-first
All I/O is async. The runtime, providers, memory, and tools all use `async/await`. Never use blocking I/O in the main thread.

### Streaming
Responses stream via `async for chunk in provider.stream_chat(...)`. The TUI widget `StreamingMarkdownWidget` receives tokens via `append_token()` and re-renders with code-fence awareness.

### Memory
Sessions and messages are persisted in SQLite via `aiosqlite`. The `MemoryManager` provides a high-level API. The database path is `~/.config/clob/clob.db`.

### Configuration
Config is loaded from `~/.config/clob/config.toml`. API keys use `env:VAR_NAME` references to avoid storing secrets. Profiles allow named provider/model configurations.

---

## Common Tasks

### Add a new provider

1. Create `clob/providers/my_provider.py` subclassing `OpenAICompatibleProvider`
2. Add to `_BUILTIN_PROVIDERS` dict in `clob/providers/registry.py`
3. Add `ProviderCapabilities` entry in `clob/providers/capabilities.py`
4. Add default config entry in `clob/config/settings.py` `_create_defaults()`
5. Write tests

### Add a new TUI screen

1. Create `clob/tui/screens/my_screen.py` extending `ModalScreen`
2. Export from `clob/tui/screens/__init__.py`
3. Add a `push_screen()` call in `clob/tui/app.py`
4. Add a keybinding if needed

### Add a new CLI command

Add a `@app.command("name")` function in `clob/main.py`.

### Add a new theme

Add to the `BUILTIN` dict in `clob/themes/__init__.py` with a `Theme(name, description, tcss)`.

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/ -k "test_analytics" -v

# With coverage
pytest tests/ --cov=clob
```

Tests use `pytest-asyncio` with `asyncio_mode = "auto"`.

---

## Code Style

- **Black** for formatting (line length 100)
- **Ruff** for linting
- Type hints on all public functions
- Docstrings on all public classes and methods
- `from __future__ import annotations` at the top of every file

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `textual` | TUI framework |
| `rich` | Terminal rendering, markdown |
| `httpx` | Async HTTP client |
| `pydantic` | Config validation |
| `aiosqlite` | Async SQLite |
| `typer` | CLI framework |
| `markdown-it-py` | Markdown parsing |
| `pygments` | Syntax highlighting |

---

## Environment Variables

| Variable | Provider |
|----------|---------|
| `OPENROUTER_API_KEY` | OpenRouter |
| `GROQ_API_KEY` | Groq |
| `NVIDIA_API_KEY` | NVIDIA Build |
| `OPENAI_API_KEY` | OpenAI (via openai_compatible) |

---

## File Locations (Runtime)

| Path | Contents |
|------|---------|
| `~/.config/clob/config.toml` | Main configuration |
| `~/.config/clob/clob.db` | SQLite database |
| `~/.config/clob/clob.log` | Application log |
| `~/.config/clob/plugins/` | User plugins |
| `~/.config/clob/themes/` | User themes |

---

## Known Gotchas

- `StreamingMarkdownWidget` throttles re-renders every 3 tokens to reduce flicker — don't change this without testing with long responses
- The `ProviderRegistry` does not auto-reload; call `load_from_config()` once on startup
- `aiosqlite.Row` must be accessed by column name (dict-style), not index
- Textual CSS class selectors use `--highlight` (double dash) for the highlighted list item, not `.active`
- The `resolve_context_refs()` function modifies the user message before it's stored — store the original, pass the resolved version to the provider

---

## Contribution Quick Reference

```bash
git clone https://github.com/crishacks/clob
cd clob
pip install -e ".[dev]"
pytest tests/ -v          # all green before PR
ruff check clob/           # no lint errors
black --check clob/        # formatted
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.
