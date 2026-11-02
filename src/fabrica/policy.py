from __future__ import annotations

from .domain import Expedient, PolicyDecision, ProcedureDefinition


class PolicyEngine:
    """Aplica el umbral de intervención de una organización."""

    _SEVERITY_RANKS = {"low": 1, "medium": 2, "high": 3, "critical": 4}

    def __init__(self, max_automatic_severity: str = "low"):
        if max_automatic_severity not in self._SEVERITY_RANKS:
            raise ValueError(f"Umbral de severidad no válido: {max_automatic_severity}")
        self.max_automatic_severity = max_automatic_severity

    def evaluate(self, procedure: ProcedureDefinition) -> PolicyDecision:
        severity = procedure.severity.lower()
        if severity not in self._SEVERITY_RANKS:
            return PolicyDecision(
                allowed=False,
                requires_human=True,
                status="blocked",
                reason=f"Severidad no clasificada: {procedure.severity}",
            )

        if self._SEVERITY_RANKS[severity] <= self._SEVERITY_RANKS[self.max_automatic_severity]:
            return PolicyDecision(
                allowed=True,
                requires_human=False,
                status="ready_for_execution",
                reason=f"Severidad {severity} dentro del umbral automático",
            )

        return PolicyDecision(
            allowed=True,
            requires_human=True,
            status="awaiting_approval",
            reason=f"Severidad {severity} supera el umbral automático",
        )

    def apply(self, expedient: Expedient, procedure: ProcedureDefinition) -> PolicyDecision:
        decision = self.evaluate(procedure)
        expedient.evidence["policy"] = {
            "severity": procedure.severity,
            "max_automatic_severity": self.max_automatic_severity,
            "allowed": decision.allowed,
            "requires_human": decision.requires_human,
            "reason": decision.reason,
        }
        expedient.move_to(decision.status)
        return decision
