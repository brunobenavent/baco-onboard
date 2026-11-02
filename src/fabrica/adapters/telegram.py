from __future__ import annotations

import json
import os
from typing import Callable, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class TelegramBotMessenger:
    """Adapter pequeño para enviar texto mediante la API oficial de bots."""

    def __init__(
        self,
        token: str,
        request_fn: Optional[Callable[[str, bytes], bytes]] = None,
    ):
        if not token:
            raise ValueError("Falta el token del bot de Telegram")
        self.token = token
        self.request_fn = request_fn or self._request

    @classmethod
    def from_environment(cls) -> "TelegramBotMessenger":
        return cls(os.environ.get("BACO_TELEGRAM_BOT_TOKEN", ""))

    def send(self, recipient: str, message: str) -> str:
        payload = urlencode({"chat_id": recipient, "text": message}).encode("utf-8")
        response = json.loads(self.request_fn(self._url(), payload).decode("utf-8"))
        if not response.get("ok"):
            raise RuntimeError(response.get("description", "Telegram rechazó el mensaje"))
        return str(response["result"]["message_id"])

    def _url(self) -> str:
        return f"https://api.telegram.org/bot{self.token}/sendMessage"

    def _request(self, url: str, data: bytes) -> bytes:
        request = Request(url, data=data, method="POST")
        with urlopen(request, timeout=20) as response:
            return response.read()
