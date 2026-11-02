import tempfile
import unittest
from pathlib import Path

from fabrica.email_process import (
    EmailAttachment,
    EmailMessage,
    SummarizePdfEmailProcess,
)


class FakePdfExtractor:
    def extract(self, path: Path) -> str:
        return "Este documento describe el cierre mensual y tres acciones pendientes."


class FakeSummarizer:
    def summarize(self, text: str) -> str:
        return "Resumen: cierre mensual y tres acciones pendientes."


class FakeMessenger:
    def __init__(self):
        self.sent = []

    def send(self, recipient: str, message: str) -> str:
        self.sent.append((recipient, message))
        return "telegram-1"


class SummarizePdfEmailProcessTests(unittest.TestCase):
    def test_summarizes_pdf_from_allowed_sender_and_delivers_to_telegram(self):
        messenger = FakeMessenger()
        process = SummarizePdfEmailProcess(
            pdf_extractor=FakePdfExtractor(),
            summarizer=FakeSummarizer(),
            messenger=messenger,
            allowed_sender="brunobenavent@gmail.com",
        )
        with tempfile.TemporaryDirectory() as directory:
            pdf_path = Path(directory) / "documento.pdf"
            pdf_path.write_bytes(b"fake pdf")
            message = EmailMessage(
                message_id="gmail-1",
                sender="brunobenavent@gmail.com",
                subject="Documento para resumir",
                attachments=[EmailAttachment("documento.pdf", pdf_path, "application/pdf")],
            )

            result = process.run(message, telegram_recipient="telegram-user-1")

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.summary, "Resumen: cierre mensual y tres acciones pendientes.")
        self.assertEqual(messenger.sent[0][0], "telegram-user-1")
        self.assertIn("Resumen:", messenger.sent[0][1])

    def test_rejects_messages_from_other_senders(self):
        process = SummarizePdfEmailProcess(
            FakePdfExtractor(), FakeSummarizer(), FakeMessenger(), "brunobenavent@gmail.com"
        )

        with self.assertRaises(PermissionError):
            process.run(
                EmailMessage("gmail-2", "otro@example.com", "Documento", []),
                telegram_recipient="telegram-user-1",
            )

    def test_rejects_email_without_pdf_attachment(self):
        process = SummarizePdfEmailProcess(
            FakePdfExtractor(), FakeSummarizer(), FakeMessenger(), "brunobenavent@gmail.com"
        )

        with self.assertRaises(ValueError):
            process.run(
                EmailMessage("gmail-3", "brunobenavent@gmail.com", "Sin PDF", []),
                telegram_recipient="telegram-user-1",
            )


if __name__ == "__main__":
    unittest.main()
