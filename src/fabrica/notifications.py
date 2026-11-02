from __future__ import annotations

from typing import Protocol

from .domain import Expedient


class Messenger(Protocol):
    def send(self, recipient: str, message: str) -> str: ...


class NotificationService:
    """Envía resultados por el canal de origen sin conocer su proveedor."""

    def __init__(self):
        self._messengers: dict[str, Messenger] = {}

    def register(self, channel: str, messenger: Messenger) -> None:
        if channel in self._messengers:
            raise ValueError(f"El canal ya está registrado: {channel}")
        self._messengers[channel] = messenger

    def notify(self, expedient: Expedient, message: str) -> str:
        try:
            messenger = self._messengers[expedient.channel]
        except KeyError as error:
            raise KeyError(f"No hay adapter para el canal: {expedient.channel}") from error

        notification_id = messenger.send(expedient.requested_by, message)
        expedient.record_event(
            "notification_sent",
            {
                "channel": expedient.channel,
                "recipient": expedient.requested_by,
                "notification_id": notification_id,
            },
        )
        expedient.evidence.setdefault("notifications", []).append(
            {"notification_id": notification_id, "message": message}
        )
        return notification_id
