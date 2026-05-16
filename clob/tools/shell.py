"""Safe shell execution tool."""

from __future__ import annotations

import asyncio
import shlex
from typing import NamedTuple


class ShellResult(NamedTuple):
    stdout: str
    stderr: str
    returncode: int


SAFE_MODE_ALLOWLIST = {
    "ls", "cat", "echo", "pwd", "date", "whoami",
    "git", "python", "python3", "pip", "uname",
}


async def run_shell(
    command: str,
    safe_mode: bool = True,
    timeout: float = 30.0,
) -> ShellResult:
    """Execute a shell command asynchronously."""
    if safe_mode:
        tokens = shlex.split(command)
        if tokens and tokens[0] not in SAFE_MODE_ALLOWLIST:
            return ShellResult(
                stdout="",
                stderr=f"Command '{tokens[0]}' not in safe mode allowlist.",
                returncode=1,
            )

    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return ShellResult("", "Command timed out.", -1)

    return ShellResult(
        stdout=stdout.decode(errors="replace"),
        stderr=stderr.decode(errors="replace"),
        returncode=proc.returncode or 0,
    )
