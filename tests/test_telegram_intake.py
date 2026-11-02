import tempfile
import unittest
from pathlib import Path

from fabrica.telegram_intake import JsonConversationStore, TelegramAutomationIntake


class FakeMessenger:
    def __init__(self):
        self.sent = []

    def send(self, recipient, message):
        self.sent.append((recipient, message))
        return f"sent-{len(self.sent)}"


class TelegramAutomationIntakeTests(unittest.TestCase):
    def test_guides_a_user_from_request_to_activation(self):
        with tempfile.TemporaryDirectory() as directory:
            messenger = FakeMessenger()
            intake = TelegramAutomationIntake(
                allowed_chat_id="123",
                messenger=messenger,
                store=JsonConversationStore(Path(directory)),
            )

            intake.handle("123", "/start")
            intake.handle("123", "Resumir PDFs que lleguen por email")
            intake.handle("123", "Cuando llegue un email de Bruno")
            intake.handle("123", "Un PDF adjunto")
            intake.handle("123", "Enviar el resumen por Telegram")

            self.assertIn("ACTIVAR", messenger.sent[-1][1])
            intake.handle("123", "ACTIVAR")

            self.assertIn("creada", messenger.sent[-1][1].lower())

    def test_ignores_another_chat(self):
        with tempfile.TemporaryDirectory() as directory:
            messenger = FakeMessenger()
            intake = TelegramAutomationIntake(
                allowed_chat_id="123",
                messenger=messenger,
                store=JsonConversationStore(Path(directory)),
            )

            handled = intake.handle("999", "Quiero automatizar algo")

            self.assertFalse(handled)
            self.assertEqual(messenger.sent, [])


if __name__ == "__main__":
    unittest.main()
