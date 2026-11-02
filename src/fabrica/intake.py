from __future__ import annotations

from typing import Protocol

from .catalog import ProcedureCatalog
from .domain import Expedient, IncomingRequest, ProcedureProposal


class ProcedureProposer(Protocol):
    def propose(self, request: IncomingRequest) -> ProcedureProposal: ...


class IntakeService:
    """Convierte una entrada externa en un expediente con procedimiento propuesto."""

    def __init__(self, catalog: ProcedureCatalog, proposer: ProcedureProposer):
        self.catalog = catalog
        self.proposer = proposer

    def accept(self, request: IncomingRequest) -> Expedient:
        proposal = self.proposer.propose(request)
        active = self.catalog.get_active(proposal.procedure_id)
        if active.version != proposal.procedure_version:
            raise ValueError(
                "La propuesta no coincide con la versión activa del procedimiento: "
                f"{proposal.procedure_id}@{proposal.procedure_version}"
            )

        expedient = Expedient.start(
            procedure_id=active.procedure_id,
            procedure_version=active.version,
            organization_id=request.organization_id,
            channel=request.channel,
            requested_by=request.requested_by,
            inputs={
                "message": request.message,
                "attachments": request.attachments,
                "external_id": request.external_id,
            },
        )
        expedient.record_event(
            "request_received",
            {"channel": request.channel, "external_id": request.external_id},
        )
        expedient.evidence["proposal"] = {
            "confidence": proposal.confidence,
            "rationale": proposal.rationale,
        }
        expedient.record_event(
            "procedure_proposed",
            {
                "procedure_id": proposal.procedure_id,
                "procedure_version": proposal.procedure_version,
                "confidence": proposal.confidence,
            },
        )
        expedient.move_to("awaiting_confirmation")
        return expedient
