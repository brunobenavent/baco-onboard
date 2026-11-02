from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional, Protocol


class ConversationStore(Protocol):
    def get(self, chat_id: str) -> dict[str, Any]: ...

    def save(self, chat_id: str, state: dict[str, Any]) -> None: ...


class TelegramMessenger(Protocol):
    def send(self, recipient: str, message: str) -> str: ...


class JsonConversationStore:
    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, chat_id: str) -> Path:
        digest = hashlib.sha256(chat_id.encode("utf-8")).hexdigest()
        return self.directory / f"conversation-{digest}.json"

    def get(self, chat_id: str) -> dict[str, Any]:
        path = self._path(chat_id)
        if not path.is_file():
            return {"phase": "new"}
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, chat_id: str, state: dict[str, Any]) -> None:
        path = self._path(chat_id)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(path)


class TelegramAutomationIntake:
    """Primer diálogo para convertir una idea en una propuesta de procedimiento."""

    def __init__(self, allowed_chat_id: str, messenger: TelegramMessenger, store: ConversationStore):
        self.allowed_chat_id = str(allowed_chat_id)
        self.messenger = messenger
        self.store = store

    def handle(self, chat_id: str, text: str) -> bool:
        if str(chat_id) != self.allowed_chat_id:
            return False

        state = self.store.get(str(chat_id))
        normalized = text.strip()
        command = normalized.upper()

        if command in {"/START", "/RESET", "CANCELAR"}:
            state = {"phase": "request"}
            self.store.save(str(chat_id), state)
            self._send(chat_id, "Soy BACO. ¿Qué quieres automatizar?")
            return True

        phase = state.get("phase", "new")
        if phase in {"new", "request"}:
            state.update({"phase": "trigger", "request": normalized})
            self.store.save(str(chat_id), state)
            self._send(chat_id, "¿Qué debe desencadenar el proceso?")
        elif phase == "trigger":
            state.update({"phase": "inputs", "trigger": normalized})
            self.store.save(str(chat_id), state)
            self._send(chat_id, "¿Qué datos, documentos o mensajes recibirá?")
        elif phase == "inputs":
            state.update({"phase": "result", "inputs": normalized})
            self.store.save(str(chat_id), state)
            self._send(chat_id, "¿Qué resultado quieres obtener y dónde entregarlo?")
        elif phase == "result":
            state.update({"phase": "confirmation", "result": normalized})
            self.store.save(str(chat_id), state)
            self._send(chat_id, self._proposal(state))
        elif phase == "confirmation":
            if command == "ACTIVAR":
                state["phase"] = "active"
                self.store.save(str(chat_id), state)
                self._send(chat_id, "Automatización creada y lista para la siguiente configuración técnica.")
            else:
                self._send(chat_id, "Responde ACTIVAR para crearla o CANCELAR para empezar de nuevo.")
        elif phase == "active":
            self._send(chat_id, "Esta automatización ya está creada. Responde /reset para diseñar otra.")
        return True

    def _proposal(self, state: dict[str, Any]) -> str:
        return (
            "Propuesta de automatización:\n\n"
            f"Qué quieres automatizar: {state['request']}\n"
            f"Desencadenante: {state['trigger']}\n"
            f"Datos recibidos: {state['inputs']}\n"
            f"Resultado: {state['result']}\n\n"
            "Responde ACTIVAR para crearla o CANCELAR para empezar de nuevo."
        )

    def _send(self, chat_id: str, message: str) -> None:
        self.messenger.send(str(chat_id), message)
