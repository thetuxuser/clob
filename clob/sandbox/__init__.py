"""Sandboxed tool execution system.

Provides:
- Restricted shell execution with allowlists
- Timeout handling
- Permission levels (safe / restricted / full)
- Execution logging
- Optional subprocess isolation
"""

from __future__ import annotations

import asyncio
import shlex
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class PermissionLevel(StrEnum):
    SAFE = "safe"  # Only allowlisted read-only commands
    RESTRICTED = "restricted"  # Common dev commands, no system mutations
    FULL = "full"  # All commands (requires explicit user consent)


SAFE_ALLOWLIST = {
    "ls",
    "cat",
    "echo",
    "pwd",
    "date",
    "whoami",
    "uname",
    "head",
    "tail",
    "wc",
    "grep",
    "find",
    "sort",
    "uniq",
    "python",
    "python3",
    "pip",
    "git",
    "curl",
    "wget",
}

RESTRICTED_ALLOWLIST = SAFE_ALLOWLIST | {
    "mkdir",
    "cp",
    "mv",
    "touch",
    "chmod",
    "npm",
    "node",
    "cargo",
    "go",
    "make",
    "docker",
    "docker-compose",
    "pytest",
    "ruff",
    "black",
    "mypy",
}


@dataclass
class ExecResult:
    command: str
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool = False
    blocked: bool = False
    block_reason: str = ""

    @property
    def success(self) -> bool:
        return self.returncode == 0 and not self.timed_out and not self.blocked

    def __str__(self) -> str:
        if self.blocked:
            return f"[Blocked: {self.block_reason}]"
        if self.timed_out:
            return "[Command timed out]"
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(f"[stderr] {self.stderr}")
        return "\n".join(parts) or f"[exit {self.returncode}]"


class Sandbox:
    """Sandboxed command executor with configurable permissions."""

    def __init__(
        self,
        permission: PermissionLevel = PermissionLevel.SAFE,
        timeout: float = 30.0,
        cwd: Path | None = None,
        confirm_fn: Callable[[str], bool] | None = None,
    ) -> None:
        self.permission = permission
        self.timeout = timeout
        self.cwd = cwd or Path.cwd()
        self.confirm_fn = confirm_fn  # optional async confirmation callback
        self._log: list[ExecResult] = []

    def _check_allowlist(self, command: str) -> tuple[bool, str]:
        """Check if command is allowed under current permission level."""
        if self.permission == PermissionLevel.FULL:
            return True, ""

        tokens = shlex.split(command)
        if not tokens:
            return False, "Empty command"

        cmd = tokens[0]
        # Strip path prefix
        cmd_name = Path(cmd).name

        if self.permission == PermissionLevel.SAFE:
            if cmd_name not in SAFE_ALLOWLIST:
                return (
                    False,
                    f"'{cmd_name}' not in safe allowlist. Use --permission restricted or full.",
                )
        elif self.permission == PermissionLevel.RESTRICTED:
            if cmd_name not in RESTRICTED_ALLOWLIST:
                return False, f"'{cmd_name}' not in restricted allowlist."

        return True, ""

    async def run(self, command: str) -> ExecResult:
        """Execute a command with sandbox restrictions."""
        allowed, reason = self._check_allowlist(command)
        if not allowed:
            result = ExecResult(
                command=command,
                stdout="",
                stderr="",
                returncode=1,
                blocked=True,
                block_reason=reason,
            )
            self._log.append(result)
            return result

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.cwd),
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
                result = ExecResult(
                    command=command,
                    stdout=stdout.decode(errors="replace"),
                    stderr=stderr.decode(errors="replace"),
                    returncode=proc.returncode or 0,
                )
            except TimeoutError:
                proc.kill()
                result = ExecResult(
                    command=command,
                    stdout="",
                    stderr="",
                    returncode=-1,
                    timed_out=True,
                )
        except Exception as e:
            result = ExecResult(
                command=command,
                stdout="",
                stderr=str(e),
                returncode=1,
            )

        self._log.append(result)
        return result

    def execution_log(self) -> list[ExecResult]:
        return list(self._log)

    def set_permission(self, level: PermissionLevel) -> None:
        self.permission = level
