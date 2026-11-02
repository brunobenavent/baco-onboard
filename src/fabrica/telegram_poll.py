from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Optional

from .telegram_intake import TelegramAutomationIntake


class TelegramPoller:
    """Consume una tanda de updates y conserva el offset para no repetirlos."""

    def __init__(self, client: Any, intake: TelegramAutomationIntake, state_dir: Path):
        self.client = client
        self.intake = intake
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.offset_path = state_dir / "telegram-offset.json"

    def poll_once(self, timeout: int = 0) -> int:
        offset = self._read_offset()
        updates = self.client.get_updates(offset=offset, timeout=timeout)
        processed = 0
        for update in updates:
            self._handle(update)
            update_id = update.get("update_id")
            if update_id is not None:
                self._write_offset(update_id + 1)
            processed += 1
        return processed

    def listen(self, timeout: int = 30, retry_delay: float = 2.0) -> None:
        """Escucha continuamente hasta recibir Ctrl-C."""
        while True:
            try:
                self.poll_once(timeout=timeout)
            except Exception as error:
                print(f"telegram-listen: {error}")
                time.sleep(retry_delay)

    def _handle(self, update: dict[str, Any]) -> None:
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text")
        if chat_id is not None and text:
            self.intake.handle(str(chat_id), text)

    def _read_offset(self) -> Optional[int]:
        if not self.offset_path.is_file():
            return None
        return json.loads(self.offset_path.read_text(encoding="utf-8"))["offset"]

    def _write_offset(self, offset: int) -> None:
        temporary = self.offset_path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"offset": offset}) + "\n", encoding="utf-8")
        temporary.replace(self.offset_path)
