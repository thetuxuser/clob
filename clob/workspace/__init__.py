"""Workspace-aware context system for AI coding workflows.

Supports:
- @file path/to/file.py   — inject single file
- @dir src/               — inject directory tree + contents
- @workspace              — inject workspace summary

Features:
- .clobignore support
- Git-aware (respects .gitignore patterns)
- Token budget management
- Syntax-aware chunking
"""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Iterator

# ── Default ignore patterns ────────────────────────────────────

DEFAULT_IGNORES = {
    "__pycache__", "*.pyc", "*.pyo", ".git", ".svn", ".hg",
    "node_modules", ".venv", "venv", "env", ".env",
    "dist", "build", "*.egg-info", ".ruff_cache", ".mypy_cache",
    ".pytest_cache", "*.log", "*.db", "*.sqlite",
    ".DS_Store", "Thumbs.db",
}

# ── Token estimator (rough: 1 token ≈ 4 chars) ────────────────

def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _load_ignore_patterns(workspace_root: Path) -> set[str]:
    patterns = set(DEFAULT_IGNORES)
    for ignore_file in [".clobignore", ".gitignore"]:
        ignore_path = workspace_root / ignore_file
        if ignore_path.exists():
            for line in ignore_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.add(line)
    return patterns


def _should_ignore(path: Path, patterns: set[str]) -> bool:
    name = path.name
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
        if fnmatch.fnmatch(str(path), pattern):
            return True
    return False


def _is_text_file(path: Path) -> bool:
    """Heuristic: check if file is likely text-readable."""
    binary_exts = {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
        ".pdf", ".zip", ".tar", ".gz", ".whl", ".exe", ".bin",
        ".pyc", ".so", ".dylib", ".db", ".sqlite",
    }
    return path.suffix.lower() not in binary_exts


def read_file_context(path: Path, max_tokens: int = 2000) -> str:
    """Read a file and return its content as a context block."""
    if not path.exists():
        return f"[File not found: {path}]"
    if not _is_text_file(path):
        return f"[Binary file: {path}]"
    try:
        content = path.read_text(errors="replace")
        # Truncate if needed
        if estimate_tokens(content) > max_tokens:
            chars = max_tokens * 4
            content = content[:chars] + f"\n... [truncated at {max_tokens} tokens]"
        lang = path.suffix.lstrip(".") or "text"
        return f"```{lang}\n# {path}\n{content}\n```"
    except Exception as e:
        return f"[Error reading {path}: {e}]"


def read_dir_context(
    root: Path,
    max_files: int = 20,
    max_tokens_per_file: int = 500,
    max_total_tokens: int = 8000,
) -> str:
    """Recursively read a directory and return context."""
    if not root.exists() or not root.is_dir():
        return f"[Directory not found: {root}]"

    ignore = _load_ignore_patterns(root)
    parts: list[str] = [f"## Directory: {root}\n"]
    tokens_used = 0
    files_included = 0

    for fpath in sorted(root.rglob("*")):
        if not fpath.is_file():
            continue
        if _should_ignore(fpath, ignore):
            continue
        if not _is_text_file(fpath):
            continue
        if files_included >= max_files:
            parts.append(f"\n[...{max_files} file limit reached]")
            break
        if tokens_used >= max_total_tokens:
            parts.append("\n[...token budget exhausted]")
            break

        block = read_file_context(fpath, max_tokens=max_tokens_per_file)
        block_tokens = estimate_tokens(block)
        if tokens_used + block_tokens > max_total_tokens:
            parts.append(f"\n[{fpath.name} skipped — token budget]")
            continue

        parts.append(block)
        tokens_used += block_tokens
        files_included += 1

    return "\n\n".join(parts)


def workspace_summary(root: Path) -> str:
    """Generate a workspace overview (file tree, no content)."""
    if not root.exists():
        return f"[Workspace not found: {root}]"

    ignore = _load_ignore_patterns(root)
    lines = [f"## Workspace: {root}\n"]
    total = 0

    for fpath in sorted(root.rglob("*")):
        if _should_ignore(fpath, ignore):
            continue
        rel = fpath.relative_to(root)
        depth = len(rel.parts) - 1
        indent = "  " * depth
        icon = "📁" if fpath.is_dir() else "📄"
        lines.append(f"{indent}{icon} {fpath.name}")
        total += 1
        if total > 200:
            lines.append("... [truncated]")
            break

    lines.append(f"\n{total} items")
    return "\n".join(lines)


def resolve_context_refs(text: str, cwd: Path | None = None) -> str:
    """
    Parse @file, @dir, @workspace references in user input and inject context.

    Example:
        "@file main.py explain this" -> injects file content + message
    """
    cwd = cwd or Path.cwd()
    injections: list[str] = []
    remaining = text

    for ref_type, pattern in [("@workspace", None), ("@dir ", None), ("@file ", None)]:
        if ref_type == "@workspace" and "@workspace" in text:
            injections.append(workspace_summary(cwd))
            remaining = remaining.replace("@workspace", "").strip()
        elif ref_type == "@dir " and "@dir " in text:
            parts = text.split("@dir ")
            for part in parts[1:]:
                dir_path = part.split()[0] if part.split() else ""
                if dir_path:
                    full = cwd / dir_path
                    injections.append(read_dir_context(full))
                    remaining = remaining.replace(f"@dir {dir_path}", "").strip()
        elif ref_type == "@file " and "@file " in text:
            parts = text.split("@file ")
            for part in parts[1:]:
                file_path = part.split()[0] if part.split() else ""
                if file_path:
                    full = cwd / file_path
                    injections.append(read_file_context(full))
                    remaining = remaining.replace(f"@file {file_path}", "").strip()

    if injections:
        context_block = "\n\n".join(injections)
        return f"{context_block}\n\n{remaining}"
    return text
