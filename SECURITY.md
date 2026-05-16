# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | ✅ Active  |
| 0.1.x   | ⚠️ Critical fixes only |
| < 0.1   | ❌ No support |

---

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Report security issues privately via:

- **GitHub Security Advisories:** [github.com/crishacks/clob/security/advisories/new](https://github.com/crishacks/clob/security/advisories/new)

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (optional)

### Response timeline

| Action | Timeline |
|--------|----------|
| Acknowledgment | Within 48 hours |
| Initial assessment | Within 5 business days |
| Fix + release | Within 30 days (critical: faster) |
| Public disclosure | After fix is released |

---

## Security Design Principles

### API Key Handling

- API keys are **never** logged, printed, or included in error messages
- Keys are loaded from environment variables or config files, never hardcoded
- The config file (`~/.config/clob/config.toml`) uses `env:VAR_NAME` references so keys are not stored in plaintext config

```toml
# Safe — key stays in environment
[providers.openrouter]
api_key = "env:OPENROUTER_API_KEY"

# Unsafe — do not do this
api_key = "sk-or-abc123"
```

### Sandboxed Execution

clob includes a sandboxed shell execution system with three permission levels:

| Level | Description |
|-------|-------------|
| `SAFE` | Read-only allowlisted commands only |
| `RESTRICTED` | Common developer tools, no system mutations |
| `FULL` | All commands — requires explicit user opt-in |

The default is `SAFE`. Users must explicitly enable higher levels.

### Network Security

- All API calls use HTTPS
- Custom provider endpoints should use HTTPS
- No telemetry or analytics data is sent without consent
- Proxy support follows standard `httpx` environment variables (`HTTPS_PROXY`, etc.)

### Plugin Security

- Plugins run in the same Python process as clob
- Only install plugins from trusted sources
- Plugin code is loaded directly — treat plugins like any third-party Python package
- Future versions may add sandboxed plugin execution

### Filesystem Access

- clob only reads files the user explicitly references (`@file`, `@dir`)
- The indexer respects `.clobignore` and `.gitignore` patterns
- No files are written without explicit user action

---

## Known Limitations

- Plugin system runs untrusted code in the same process (planned: sandbox)
- Config file is stored in plaintext (planned: optional encryption)
- No built-in rate limiting on provider requests

---

## Dependency Security

We use `pip-audit` in CI to scan for known vulnerabilities in dependencies. Run locally:

```bash
pip install pip-audit
pip-audit
```

---

## Responsible Disclosure

We follow responsible disclosure practices and will:

1. Credit reporters in release notes (unless anonymity is requested)
2. Work collaboratively on fixes
3. Coordinate public disclosure timing with reporters

Thank you for helping keep clob secure.
