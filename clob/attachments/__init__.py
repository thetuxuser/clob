"""Multimodal attachment handling for clob.

Supports: images, PDFs, text files, code files.
Converts to provider-compatible message formats.
"""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
SUPPORTED_TEXT_EXTS = {
    ".txt", ".md", ".py", ".js", ".ts", ".go", ".rs", ".java",
    ".c", ".cpp", ".h", ".css", ".html", ".json", ".yaml", ".yml",
    ".toml", ".sh", ".sql", ".xml",
}


@dataclass
class Attachment:
    path: Path
    mime_type: str
    data: bytes
    filename: str

    @property
    def is_image(self) -> bool:
        return self.mime_type.startswith("image/")

    @property
    def is_text(self) -> bool:
        return self.mime_type.startswith("text/") or self.path.suffix in SUPPORTED_TEXT_EXTS

    @property
    def is_pdf(self) -> bool:
        return self.mime_type == "application/pdf"

    def to_base64(self) -> str:
        return base64.standard_b64encode(self.data).decode()

    def to_openai_content_part(self) -> dict:
        """Convert to OpenAI-compatible vision content part."""
        if self.is_image:
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{self.mime_type};base64,{self.to_base64()}"
                },
            }
        elif self.is_text:
            try:
                text = self.data.decode(errors="replace")
            except Exception:
                text = f"[Binary file: {self.filename}]"
            return {"type": "text", "text": f"```\n# {self.filename}\n{text}\n```"}
        else:
            return {"type": "text", "text": f"[Attached file: {self.filename} ({self.mime_type})]"}

    def preview(self, max_chars: int = 200) -> str:
        if self.is_image:
            return f"🖼 {self.filename} ({len(self.data) // 1024}KB image)"
        if self.is_text:
            try:
                text = self.data.decode(errors="replace")[:max_chars]
                return f"📄 {self.filename}\n{text}..."
            except Exception:
                pass
        return f"📎 {self.filename} ({self.mime_type})"


def load_attachment(path: Path) -> Attachment:
    """Load a file as an Attachment."""
    mime, _ = mimetypes.guess_type(str(path))
    if mime is None:
        # Fallback detection
        if path.suffix in SUPPORTED_IMAGE_EXTS:
            mime = f"image/{path.suffix.lstrip('.')}"
        elif path.suffix in SUPPORTED_TEXT_EXTS:
            mime = "text/plain"
        else:
            mime = "application/octet-stream"

    return Attachment(
        path=path,
        mime_type=mime,
        data=path.read_bytes(),
        filename=path.name,
    )


def attachments_to_messages(
    text: str,
    attachments: list[Attachment],
) -> list[dict]:
    """Build OpenAI-compatible content list from text + attachments."""
    if not attachments:
        return [{"role": "user", "content": text}]

    content = []
    # Add attachments first
    for att in attachments:
        content.append(att.to_openai_content_part())
    # Then the text
    content.append({"type": "text", "text": text})
    return [{"role": "user", "content": content}]
