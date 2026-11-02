from __future__ import annotations

from typing import Protocol

from .catalog import ProcedureCatalog
from .domain import Expedient, IncomingRequest
from .intake import IntakeService
from .policy import PolicyEngine


class ExpedientRepository(Protocol):
    def save(self, expedient: Expedient) -> None: ...


class ProcessRuntime:
    """Orquesta la entrada, selección, política y persistencia inicial."""

    def __init__(
        self,
        intake: IntakeService,
        catalog: ProcedureCatalog,
        policy: PolicyEngine,
        expedient_repository: ExpedientRepository | None = None,
    ):
        self.intake = intake
        self.catalog = catalog
        self.policy = policy
        self.expedient_repository = expedient_repository

    def receive(self, request: IncomingRequest) -> Expedient:
        expedient = self.intake.accept(request)
        procedure = self.catalog.get(expedient.procedure_id, expedient.procedure_version)
        self.policy.apply(expedient, procedure)
        if self.expedient_repository is not None:
            self.expedient_repository.save(expedient)
        return expedient
