from __future__ import annotations

from .domain import Expedient


class ApprovalService:
    """Registra la decisión humana que desbloquea o detiene un expediente."""

    def approve(self, expedient: Expedient, decided_by: str, comment: str = "") -> None:
        self._decide(expedient, "approved", "ready_for_execution", "approval_granted", decided_by, comment)

    def reject(self, expedient: Expedient, decided_by: str, comment: str = "") -> None:
        self._decide(expedient, "rejected", "rejected", "approval_rejected", decided_by, comment)

    def request_changes(self, expedient: Expedient, decided_by: str, comment: str = "") -> None:
        self._decide(
            expedient,
            "changes_requested",
            "changes_requested",
            "changes_requested",
            decided_by,
            comment,
        )

    def _decide(
        self,
        expedient: Expedient,
        decision: str,
        status: str,
        event_type: str,
        decided_by: str,
        comment: str,
    ) -> None:
        if expedient.status != "awaiting_approval":
            raise ValueError("El expediente no está esperando una aprobación")

        expedient.evidence["approval"] = {
            "decision": decision,
            "decided_by": decided_by,
            "comment": comment,
        }
        expedient.move_to(status)
        expedient.record_event(
            event_type,
            {"decided_by": decided_by, "comment": comment, "decision": decision},
        )
