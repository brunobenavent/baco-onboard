from __future__ import annotations

import json
import re
from pathlib import Path

from ..email_process import EmailAttachment, EmailMessage


class LocalJsonEmailReader:
    """Lee un email de prueba desde un JSON local."""

    def read(self, path: Path) -> EmailMessage:
        data = json.loads(path.read_text(encoding="utf-8"))
        attachments = [
            EmailAttachment(
                filename=item["filename"],
                path=(path.parent / item["path"]).resolve(),
                content_type=item.get("content_type", ""),
            )
            for item in data.get("attachments", [])
        ]
        return EmailMessage(
            message_id=data["message_id"],
            sender=data["sender"],
            subject=data["subject"],
            attachments=attachments,
        )


class FileMessenger:
    """Simula Telegram escribiendo cada mensaje en un buzón local."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def send(self, recipient: str, message: str) -> str:
        existing = sorted(self.directory.glob(f"{recipient}-*.txt"))
        message_id = f"{recipient}-{len(existing) + 1}"
        (self.directory / f"{message_id}.txt").write_text(message, encoding="utf-8")
        return message_id


class SimpleSummarizer:
    """Resumen local determinista para validar el circuito sin un modelo externo."""

    def __init__(self, max_sentences: int = 3):
        self.max_sentences = max_sentences

    def summarize(self, text: str) -> str:
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]
        return " ".join(sentences[: self.max_sentences])
