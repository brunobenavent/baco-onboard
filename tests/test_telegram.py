import json
import unittest
from urllib.parse import parse_qs

from fabrica.adapters.telegram import TelegramBotMessenger


class TelegramAdapterTests(unittest.TestCase):
    def test_sends_message_through_the_bot_api_contract(self):
        calls = []

        def request(url, data):
            calls.append((url, data))
            return json.dumps({"ok": True, "result": {"message_id": 42}}).encode()

        messenger = TelegramBotMessenger("secret-token", request_fn=request)

        message_id = messenger.send("12345", "Prueba BACO")

        self.assertEqual(message_id, "42")
        self.assertIn("/botsecret-token/sendMessage", calls[0][0])
        self.assertEqual(parse_qs(calls[0][1].decode())["chat_id"], ["12345"])
        self.assertEqual(parse_qs(calls[0][1].decode())["text"], ["Prueba BACO"])

    def test_rejects_an_unsuccessful_telegram_response(self):
        def request(url, data):
            return json.dumps({"ok": False, "description": "Chat not found"}).encode()

        messenger = TelegramBotMessenger("secret-token", request_fn=request)

        with self.assertRaises(RuntimeError):
            messenger.send("missing", "Prueba BACO")


if __name__ == "__main__":
    unittest.main()
