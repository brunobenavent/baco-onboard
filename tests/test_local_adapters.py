import json
import tempfile
import unittest
from pathlib import Path

from fabrica.adapters.local import FileMessenger, LocalJsonEmailReader, SimpleSummarizer


class LocalAdaptersTests(unittest.TestCase):
    def test_reads_email_json_and_resolves_attachment_relative_to_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            email_file = root / "email.json"
            pdf_file = root / "documento.pdf"
            pdf_file.write_bytes(b"pdf")
            email_file.write_text(
                json.dumps(
                    {
                        "message_id": "local-1",
                        "sender": "brunobenavent@gmail.com",
                        "subject": "Documento",
                        "attachments": [
                            {
                                "filename": "documento.pdf",
                                "path": "documento.pdf",
                                "content_type": "application/pdf",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            message = LocalJsonEmailReader().read(email_file)

            self.assertEqual(message.sender, "brunobenavent@gmail.com")
            self.assertEqual(message.attachments[0].path, pdf_file.resolve())

    def test_writes_a_telegram_like_outbox_message(self):
        with tempfile.TemporaryDirectory() as directory:
            messenger = FileMessenger(Path(directory))

            message_id = messenger.send("local-telegram", "Resumen de prueba")

            self.assertEqual(message_id, "local-telegram-1")
            output = Path(directory) / "local-telegram-1.txt"
            self.assertEqual(output.read_text(encoding="utf-8"), "Resumen de prueba")

    def test_simple_summarizer_is_deterministic(self):
        summary = SimpleSummarizer(max_sentences=2).summarize(
            "Primera frase. Segunda frase. Tercera frase."
        )

        self.assertEqual(summary, "Primera frase. Segunda frase.")


if __name__ == "__main__":
    unittest.main()
