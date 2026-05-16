# Contributing to clob

> Thank you for helping build the universal AI terminal platform.

We welcome contributions of all kinds — bug fixes, features, documentation, themes, providers, and plugins.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Adding a Provider](#adding-a-provider)
- [Adding a Theme](#adding-a-theme)
- [Writing Tests](#writing-tests)
- [Commit Messages](#commit-messages)
- [Getting Help](#getting-help)

---

## Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.

---

## Getting Started

1. **Fork** the repository: [github.com/crishacks/clob](https://github.com/crishacks/clob)
2. **Clone** your fork:
   ```bash
   git clone https://github.com/yourusername/clob.git
   cd clob
   ```
3. **Create a branch** for your work:
   ```bash
   git checkout -b feat/my-feature
   ```

---

## Development Setup

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Launch TUI
clob

# Run tests
pytest tests/ -v

# Lint and format
ruff check clob/
black clob/
```

---

## Project Structure

```
clob/
├── clob/
│   ├── tui/           # Textual TUI — app, screens, widgets, themes
│   ├── core/          # Runtime, streaming, routing
│   ├── providers/     # AI provider implementations + capabilities
│   ├── memory/        # SQLite session/message persistence
│   ├── analytics/     # Token and cost tracking
│   ├── workspace/     # Workspace context (@file, @dir, @workspace)
│   ├── indexing/      # File indexer with language detection
│   ├── rendering/     # Markdown and image rendering
│   ├── sandbox/       # Safe sandboxed command execution
│   ├── themes/        # TUI theme system (dark, light, cyberpunk, nord)
│   ├── attachments/   # Multimodal file attachments
│   ├── plugins/       # Plugin loader system
│   ├── agents/        # AI agent foundations
│   ├── tools/         # Shell and filesystem tools
│   ├── config/        # Settings, profiles, config loader
│   └── main.py        # Typer CLI entry point
├── tests/
├── docs/
└── scripts/
```

---

## How to Contribute

### Bug Reports

Open an issue with:
- `clob --version` output
- OS and Python version
- Steps to reproduce
- Expected vs. actual behavior

### Feature Requests

Open an issue with:
- The problem you're solving
- Your proposed solution
- Alternatives considered

### Code Contributions

- Bug fixes → `main` branch
- New features → `dev` branch
- Documentation → any branch

---

## Pull Request Process

1. All tests must pass: `pytest tests/ -v`
2. Linting must pass: `ruff check clob/ && black --check clob/`
3. Update docs for new features
4. Add tests for new functionality
5. Fill out the PR template
6. Request a maintainer review

---

## Coding Standards

- **Formatter:** `black`, line length 100
- **Linter:** `ruff`
- **Type hints:** Required on all public functions
- **Docstrings:** Required on all public classes and functions
- **Async-first:** Use `async/await` everywhere. Never block the event loop.
- **Modular:** One concern per module.
- **Provider-agnostic:** No provider logic outside `providers/`.
- **No secrets in code:** Keys come from env vars or config files only.

---

## Adding a Provider

1. Create `clob/providers/my_provider.py`:

```python
from .openai_compatible import OpenAICompatibleProvider
from ..config.settings import ProviderConfig

class MyProvider(OpenAICompatibleProvider):
    name = "my-provider"
    def __init__(self, config: ProviderConfig) -> None:
        config.base_url = config.base_url or "https://api.my-provider.com/v1"
        super().__init__(config)
```

2. Register in `clob/providers/registry.py`
3. Add capabilities in `clob/providers/capabilities.py`
4. Add tests and documentation

---

## Adding a Theme

Add to `BUILTIN` in `clob/themes/__init__.py` or place a `.tcss` file in `~/.config/clob/themes/`:

```tcss
Screen { background: #1e1e2e; color: #cdd6f4; }
#sidebar { background: #181825; border-right: solid #313244; }
```

---

## Writing Tests

```python
@pytest.mark.asyncio
async def test_my_feature(tmp_path):
    from clob.my_module import my_function
    result = await my_function(tmp_path)
    assert result is not None
```

---

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Anthropic provider
fix: resolve streaming hang on Groq timeout
docs: update provider setup guide
test: add workspace indexer edge cases
chore: bump textual to 0.60.0
```

---

## Getting Help

- [GitHub Discussions](https://github.com/crishacks/clob/discussions)
- [Open an Issue](https://github.com/crishacks/clob/issues)

Thank you for contributing to clob!
