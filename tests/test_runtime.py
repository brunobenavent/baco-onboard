import tempfile
import unittest
from pathlib import Path

from fabrica.catalog import ProcedureCatalog
from fabrica.domain import IncomingRequest, ProcedureDefinition, ProcedureProposal
from fabrica.intake import IntakeService
from fabrica.policy import PolicyEngine
from fabrica.repositories import JsonExpedientRepository
from fabrica.runtime import ProcessRuntime


class FakeProposer:
    def __init__(self, proposal):
        self.proposal = proposal

    def propose(self, request):
        return self.proposal


class ProcessRuntimeTests(unittest.TestCase):
    def _runtime(self, severity):
        catalog = ProcedureCatalog()
        catalog.register(
            ProcedureDefinition(
                procedure_id="process-request",
                version="1.0",
                name="Procesar petición",
                description="Procesa una petición interna.",
                severity=severity,
            )
        )
        catalog.activate("process-request", "1.0")
        intake = IntakeService(
            catalog,
            FakeProposer(ProcedureProposal("process-request", "1.0", 0.95, "Coincide con el proceso.")),
        )
        return catalog, ProcessRuntime(intake, catalog, PolicyEngine("low"))

    def test_receives_persists_and_allows_a_low_risk_request(self):
        catalog, runtime = self._runtime("low")
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonExpedientRepository(Path(directory))
            runtime.expedient_repository = repository
            expedient = runtime.receive(
                IncomingRequest("empresa-demo", "email", "mail-1", "user-42", "Procesa esto", [])
            )

            self.assertEqual(expedient.status, "ready_for_execution")
            self.assertIsNotNone(repository.get(expedient.id))
            self.assertEqual(expedient.timeline[-1]["type"], "status_changed")

    def test_routes_high_risk_request_to_human_approval(self):
        _, runtime = self._runtime("high")

        expedient = runtime.receive(
            IncomingRequest("empresa-demo", "telegram", "msg-1", "user-42", "Hazlo", [])
        )

        self.assertEqual(expedient.status, "awaiting_approval")


if __name__ == "__main__":
    unittest.main()
