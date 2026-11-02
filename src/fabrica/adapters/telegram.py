from __future__ import annotations

import json
import os
from typing import Any, Callable, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class TelegramBotMessenger:
    """Adapter pequeño para enviar texto mediante la API oficial de bots."""

    def __init__(
        self,
        token: str,
        request_fn: Optional[Callable[[str, Optional[bytes]], bytes]] = None,
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

    def get_updates(self, offset: Optional[int] = None, timeout: int = 0) -> list[dict[str, Any]]:
        params = {"timeout": str(timeout)}
        if offset is not None:
            params["offset"] = str(offset)
        url = f"https://api.telegram.org/bot{self.token}/getUpdates?{urlencode(params)}"
        response = json.loads(self.request_fn(url, None).decode("utf-8"))
        if not response.get("ok"):
            raise RuntimeError(response.get("description", "Telegram rechazó getUpdates"))
        return response.get("result", [])

    def _url(self) -> str:
        return f"https://api.telegram.org/bot{self.token}/sendMessage"

    def _request(self, url: str, data: Optional[bytes]) -> bytes:
        request = Request(url, data=data, method="POST" if data is not None else "GET")
        with urlopen(request, timeout=20) as response:
            return response.read()
