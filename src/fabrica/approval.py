from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

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

    def set_expiry(self, expedient: Expedient, expires_at: str) -> None:
        approval = expedient.evidence.setdefault("approval", {})
        approval["expires_at"] = expires_at
        expedient.record_event("approval_deadline_set", {"expires_at": expires_at})

    def expire_if_due(
        self, expedient: Expedient, now: Optional[datetime] = None
    ) -> bool:
        if expedient.status != "awaiting_approval":
            return False
        expires_at = expedient.evidence.get("approval", {}).get("expires_at")
        if not expires_at:
            return False
        deadline = datetime.fromisoformat(expires_at)
        current_time = now or datetime.now(timezone.utc)
        if deadline > current_time:
            return False
        expedient.move_to("approval_expired")
        expedient.record_event("approval_expired", {"expires_at": expires_at})
        return True

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
