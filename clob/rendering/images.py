"""Terminal image rendering layer.

Auto-detects terminal capabilities and uses:
1. Kitty Graphics Protocol
2. iTerm2 inline images
3. Sixel
4. ASCII art fallback

Usage:
    renderer = ImageRenderer()
    await renderer.render("path/to/image.png")
"""

from __future__ import annotations

import base64
import os
from pathlib import Path


class TerminalCapability:
    """Detect terminal image rendering capabilities."""

    @staticmethod
    def detect() -> str:
        """Return best available renderer: 'kitty' | 'iterm' | 'sixel' | 'ascii'."""
        term = os.environ.get("TERM", "")
        term_program = os.environ.get("TERM_PROGRAM", "")
        os.environ.get("COLORTERM", "")

        if "kitty" in term:
            return "kitty"
        if term_program in ("iTerm.app", "WezTerm"):
            return "iterm"
        if "sixel" in term or os.environ.get("TERM_FEATURES", ""):
            return "sixel"
        return "ascii"


class ImageRenderer:
    """Render images to terminal using best available protocol."""

    def __init__(self, protocol: str | None = None) -> None:
        self.protocol = protocol or TerminalCapability.detect()

    async def render(self, path: str | Path, width: int = 40) -> str:
        """
        Render image and return the escape sequence string or ASCII art.
        Returns a string to be printed/displayed.
        """
        path = Path(path)
        if not path.exists():
            return f"[Image not found: {path}]"

        if self.protocol == "kitty":
            return self._render_kitty(path)
        elif self.protocol == "iterm":
            return self._render_iterm(path)
        elif self.protocol == "sixel":
            return self._render_sixel_fallback(path)
        else:
            return self._render_ascii(path)

    def _render_kitty(self, path: Path) -> str:
        """Kitty Graphics Protocol (APC escape sequences)."""
        try:
            data = base64.standard_b64encode(path.read_bytes()).decode()
            # Kitty protocol: ESC_G + base64 + ESC_\
            chunks = [data[i : i + 4096] for i in range(0, len(data), 4096)]
            result = []
            for i, chunk in enumerate(chunks):
                m = 1 if i < len(chunks) - 1 else 0
                if i == 0:
                    result.append(f"\033_Ga=T,f=100,m={m};{chunk}\033\\")
                else:
                    result.append(f"\033_Gm={m};{chunk}\033\\")
            return "".join(result)
        except Exception as e:
            return f"[Kitty render error: {e}]"

    def _render_iterm(self, path: Path) -> str:
        """iTerm2 inline image protocol."""
        try:
            data = base64.standard_b64encode(path.read_bytes()).decode()
            size = path.stat().st_size
            name = base64.standard_b64encode(path.name.encode()).decode()
            return f"\033]1337;File=name={name};size={size};inline=1:{data}\a"
        except Exception as e:
            return f"[iTerm render error: {e}]"

    def _render_sixel_fallback(self, path: Path) -> str:
        """Attempt sixel via img2sixel if available, else fallback."""
        try:
            import subprocess

            result = subprocess.run(["img2sixel", str(path)], capture_output=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.decode(errors="replace")
        except (FileNotFoundError, Exception):
            pass
        return self._render_ascii(path)

    def _render_ascii(self, path: Path) -> str:
        """ASCII art fallback using simple block characters."""
        try:
            # Try to use Pillow if available
            from PIL import Image

            img = Image.open(path).convert("L")  # grayscale
            img.thumbnail((60, 30))
            w, h = img.size
            chars = " .:-=+*#%@"
            lines = []
            for y in range(h):
                row = ""
                for x in range(w):
                    pixel = img.getpixel((x, y))
                    row += chars[pixel * (len(chars) - 1) // 255]
                lines.append(row)
            return "\n".join(lines)
        except ImportError:
            size_kb = path.stat().st_size // 1024
            return f"[Image: {path.name} ({size_kb}KB) — install Pillow for preview]"
        except Exception as e:
            return f"[Image preview error: {e}]"
