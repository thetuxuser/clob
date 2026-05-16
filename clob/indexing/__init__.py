"""Workspace file indexer."""

from __future__ import annotations

import fnmatch
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

DEFAULT_IGNORES = {
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".git",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    "*.egg-info",
    ".ruff_cache",
    ".mypy_cache",
    ".pytest_cache",
    "*.log",
    "*.db",
    "*.sqlite",
    ".DS_Store",
}
BINARY_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".whl",
    ".exe",
    ".bin",
    ".pyc",
    ".so",
    ".dylib",
    ".sqlite",
}


def _is_text(path: Path) -> bool:
    return path.suffix.lower() not in BINARY_EXTS


def _should_ignore(path: Path, patterns: set[str]) -> bool:
    name = path.name
    return any(fnmatch.fnmatch(name, p) or fnmatch.fnmatch(str(path), p) for p in patterns)


def _load_ignores(root: Path) -> set[str]:
    pats = set(DEFAULT_IGNORES)
    for f in [".clobignore", ".gitignore"]:
        fp = root / f
        if fp.exists():
            for line in fp.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    pats.add(line)
    return pats


def _tokens(text: str) -> int:
    return max(1, len(text) // 4)


@dataclass
class IndexedFile:
    path: Path
    rel_path: str
    size_bytes: int
    estimated_tokens: int
    last_modified: datetime
    file_hash: str
    language: str = ""


@dataclass
class WorkspaceIndex:
    root: Path
    files: list[IndexedFile] = field(default_factory=list)
    indexed_at: datetime = field(default_factory=lambda: __import__("datetime").datetime.now())

    @property
    def total_files(self) -> int:
        return len(self.files)

    @property
    def total_tokens(self) -> int:
        return sum(f.estimated_tokens for f in self.files)

    @property
    def total_size_bytes(self) -> int:
        return sum(f.size_bytes for f in self.files)

    def search(self, query: str) -> list[IndexedFile]:
        q = query.lower()
        return [f for f in self.files if q in f.rel_path.lower()]

    def by_language(self) -> dict[str, list[IndexedFile]]:
        r: dict[str, list[IndexedFile]] = {}
        for f in self.files:
            r.setdefault(f.language, []).append(f)
        return r

    def stats_report(self) -> str:
        by_lang = self.by_language()
        lines = [
            f"Workspace: {self.root}",
            f"Files:     {self.total_files}",
            f"Size:      {self.total_size_bytes / 1024:.1f} KB",
            f"Tokens:    ~{self.total_tokens:,}",
            "",
            "By language:",
        ]
        for lang, files in sorted(by_lang.items(), key=lambda x: -len(x[1])):
            lines.append(f"  {lang or 'other':12} {len(files):4} files")
        return "\n".join(lines)


def index_workspace(root: Path) -> WorkspaceIndex:
    root = root.resolve()
    ignore = _load_ignores(root)
    idx = WorkspaceIndex(root=root)
    for fpath in sorted(root.rglob("*")):
        if not fpath.is_file() or _should_ignore(fpath, ignore) or not _is_text(fpath):
            continue
        try:
            stat = fpath.stat()
            content = fpath.read_bytes()
            file_hash = hashlib.md5(content, usedforsecurity=False).hexdigest()[:8]
            tokens = _tokens(content.decode(errors="replace"))
            idx.files.append(
                IndexedFile(
                    path=fpath,
                    rel_path=str(fpath.relative_to(root)),
                    size_bytes=stat.st_size,
                    estimated_tokens=tokens,
                    last_modified=datetime.fromtimestamp(stat.st_mtime),
                    file_hash=file_hash,
                    language=fpath.suffix.lstrip(".") or "text",
                )
            )
        except Exception:
            continue
    return idx
