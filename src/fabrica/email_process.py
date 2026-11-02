from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class EmailAttachment:
    filename: str
    path: Path
    content_type: str


@dataclass(frozen=True)
class EmailMessage:
    message_id: str
    sender: str
    subject: str
    attachments: list[EmailAttachment]


@dataclass(frozen=True)
class SummaryDelivery:
    status: str
    summary: str
    notification_id: str


class PdfTextExtractor(Protocol):
    def extract(self, path: Path) -> str: ...


class Summarizer(Protocol):
    def summarize(self, text: str) -> str: ...


class TelegramMessenger(Protocol):
    def send(self, recipient: str, message: str) -> str: ...


class SummarizePdfEmailProcess:
    """Primer procedimiento realista: email permitido → PDF → resumen → Telegram."""

    def __init__(
        self,
        pdf_extractor: PdfTextExtractor,
        summarizer: Summarizer,
        messenger: TelegramMessenger,
        allowed_sender: str,
    ):
        self.pdf_extractor = pdf_extractor
        self.summarizer = summarizer
        self.messenger = messenger
        self.allowed_sender = allowed_sender

    def run(self, message: EmailMessage, telegram_recipient: str) -> SummaryDelivery:
        if message.sender.lower() != self.allowed_sender.lower():
            raise PermissionError(f"Remitente no permitido: {message.sender}")

        pdfs = [
            attachment
            for attachment in message.attachments
            if attachment.content_type == "application/pdf"
            or attachment.filename.lower().endswith(".pdf")
        ]
        if len(pdfs) != 1:
            raise ValueError("El email debe contener exactamente un PDF")

        text = self.pdf_extractor.extract(pdfs[0].path)
        if not text.strip():
            raise ValueError("El PDF no contiene texto extraíble")
        summary = self.summarizer.summarize(text)
        notification_id = self.messenger.send(
            telegram_recipient,
            f"Resumen de: {message.subject}\n\n{summary}",
        )
        return SummaryDelivery("completed", summary, notification_id)
