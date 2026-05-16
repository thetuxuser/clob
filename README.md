# clob

> **Universal AI in your terminal.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/clob.svg)](https://pypi.org/project/clob/)
[![CI](https://github.com/crishacks/clob/actions/workflows/ci.yml/badge.svg)](https://github.com/crishacks/clob/actions)

clob is an open-source universal AI terminal platform with a modern TUI. Connect any AI provider, stream responses, manage sessions, and build AI workflows — all from your terminal.

```
+----------------------------------------------------------+
|  clob                              Sat May 17  12:00:00  |
+---------------------------+------------------------------+
|  clob v0.2                | openrouter › gpt-4o-mini     |
|                           | 👁 vision  🔧 tools          |
|  💬 Fix the auth bug      +------------------------------+
|  💬 Write unit tests      |  ▶ You                       |
|  💬 Docker setup help     |  @file main.py explain this  |
|  💬 Explain async/await   |                              |
|                           |  ◆ AI                        |
|                           |  The `main.py` file defines  |
|                           |  your Typer CLI entry point. |
|                           |  Here's a breakdown...       |
|  [ + New Chat ]           |                              |
+---------------------------+------------------------------+
|  Type a message… @file, @dir, @workspace, Ctrl+P         |
+----------------------------------------------------------+
| clob v0.2 │ openrouter › gpt-4o-mini  │ ● ready         |
+----------------------------------------------------------+
```

## Features

- **Modern TUI** — Textual-powered UI with sidebar, streaming chat, command palette (`Ctrl+P`)
- **Universal Providers** — OpenRouter, Groq, NVIDIA Build, Ollama, any OpenAI-compatible API
- **Workspace Context** — `@file main.py`, `@dir src/`, `@workspace` inject context into prompts
- **Real-time Streaming** — Markdown rendering with code-fence awareness, reduced flicker
- **Analytics** — Token counts and estimated cost tracked live per session
- **Persistent Memory** — SQLite-backed sessions, messages, full-text search
- **Themes** — dark, light, cyberpunk, nord + custom user themes
- **Sandbox Execution** — Safe shell with `SAFE/RESTRICTED/FULL` permission levels
- **Plugin System** — Extend with custom providers, themes, tools, and agents
- **Cross-platform** — Linux, macOS, Windows

---

## Installation

### pip (all platforms)

```bash
pip install clob
```

### Homebrew (macOS / Linux)

```bash
brew tap crishacks/tap
brew install clob
```

### Scoop (Windows)

```powershell
scoop bucket add crishacks https://github.com/crishacks/scoop-clob
scoop install crishacks/clob
```

### Chocolatey (Windows)

```powershell
choco install clob
```

### Docker

```bash
docker run -it --rm \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  ghcr.io/crishacks/clob:latest
```

### From source

```bash
git clone https://github.com/crishacks/clob
cd clob
pip install -e .
```

---

## Quick Start

```bash
# Set API key
export OPENROUTER_API_KEY="sk-or-..."

# Launch TUI
clob

# Single message
clob chat "Explain async/await in Python"

# Use Groq (fast inference)
clob chat "Hello" --provider groq --model llama3-8b-8192

# Check setup
clob doctor
```

---

## Provider Setup

Set API keys as environment variables:

```bash
export OPENROUTER_API_KEY="sk-or-..."
export GROQ_API_KEY="gsk_..."
export NVIDIA_API_KEY="nvapi-..."
```

Or configure `~/.config/clob/config.toml`:

```toml
[default]
provider = "openrouter"
model = "openai/gpt-4o-mini"

[providers.openrouter]
base_url = "https://openrouter.ai/api/v1"
api_key = "env:OPENROUTER_API_KEY"

[providers.groq]
base_url = "https://api.groq.com/openai/v1"
api_key = "env:GROQ_API_KEY"

# Named profiles
[profiles.work]
provider = "openrouter"
model = "anthropic/claude-sonnet-4"

[profiles.local]
provider = "ollama"
model = "llama3"
```

### Custom OpenAI-Compatible Provider

```toml
[providers.my-provider]
base_url = "https://api.example.com/v1"
api_key = "env:MY_API_KEY"
chat_endpoint = "/chat/completions"
```

---

## Workspace Context

Inject files and directories directly into your prompts:

```
@file main.py explain this code
@dir src/ what does this module do?
@workspace give me an overview of this project
```

---

## TUI Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+P` | Command palette |
| `Ctrl+N` | New chat session |
| `Ctrl+S` | Settings |
| `Ctrl+U` | Usage / token analytics |
| `Ctrl+F` | Search memory |
| `Ctrl+B` | Toggle sidebar |
| `Ctrl+L` | Clear chat |
| `Ctrl+Q` | Quit |
| `Enter` | Send message |
| `Escape` | Focus input |

---

## CLI Commands

```bash
clob                          # Launch TUI
clob chat "message"           # Send a message
clob chat "msg" -p groq       # Use specific provider
clob models                   # List available models
clob providers                # List configured providers
clob config --show            # Show config
clob config --edit            # Edit in $EDITOR
clob memory --sessions        # List sessions
clob memory --search query    # Search history
clob session --export 5       # Export session #5 as markdown
clob session --export 5 -f json  # Export as JSON
clob ollama list              # List local Ollama models
clob ollama pull llama3       # Pull a model
clob workspace stats          # Show workspace file stats
clob workspace index          # Index current workspace
clob theme list               # List themes
clob theme set cyberpunk      # Set theme
clob plugins list             # List plugins
clob plugins install <pkg>    # Install a plugin
clob usage                    # Show usage report
clob doctor                   # Diagnose installation
```

---

## Themes

```bash
clob theme list
# dark, light, cyberpunk, nord

clob theme set nord
```

Place custom `.tcss` files in `~/.config/clob/themes/` to create your own themes.

---

## Ollama (Local Models)

```bash
# Start Ollama
ollama serve

# List local models
clob ollama list

# Pull a model
clob ollama pull llama3

# Use in TUI — select "ollama" as provider
```

---

## Docker

```bash
# Basic
docker run -it --rm \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  ghcr.io/crishacks/clob:latest

# With Ollama
docker-compose --profile ollama up
```

---

## Plugin Development

Create `~/.config/clob/plugins/my-plugin/plugin.py`:

```python
from clob.plugins import Plugin

class ClobPlugin(Plugin):
    name = "my-plugin"
    version = "1.0.0"
    description = "My custom clob plugin"

    def on_load(self, app) -> None:
        print("Plugin loaded!")
```

---

## Development

```bash
git clone https://github.com/crishacks/clob
cd clob
pip install -e ".[dev]"

pytest tests/ -v     # Run tests (36 tests)
ruff check clob/     # Lint
black clob/          # Format
clob doctor          # Check setup
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full contributor guide.

---

## Documentation

| Doc | Description |
|-----|-------------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contributor guide |
| [SECURITY.md](SECURITY.md) | Security policy and reporting |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community standards |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [AGENTS.md](docs/AGENTS.md) | Agent architecture |
| [CLAUDE.md](CLAUDE.md) | AI assistant context file |

---

## Roadmap

- [ ] Anthropic Claude native provider
- [ ] MCP (Model Context Protocol) support
- [ ] Multi-agent workflows
- [ ] Image generation in TUI
- [ ] Voice input
- [ ] Theme marketplace
- [ ] VS Code extension

---

## Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE).
