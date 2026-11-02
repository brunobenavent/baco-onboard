import unittest

from fabrica.catalog import ProcedureCatalog
from fabrica.domain import IncomingRequest, ProcedureDefinition, ProcedureProposal
from fabrica.intake import IntakeService


class FakeProposer:
    def __init__(self, proposal):
        self.proposal = proposal

    def propose(self, request):
        return self.proposal


class IntakeServiceTests(unittest.TestCase):
    def test_creates_expedient_with_the_proposed_active_procedure(self):
        catalog = ProcedureCatalog()
        catalog.register(
            ProcedureDefinition(
                procedure_id="prepare-report",
                version="2.0",
                name="Preparar informe",
                description="Prepara un informe interno.",
                severity="low",
            )
        )
        catalog.activate("prepare-report", "2.0")
        service = IntakeService(
            catalog,
            FakeProposer(ProcedureProposal("prepare-report", "2.0", 0.94, "La petición solicita un informe.")),
        )

        expedient = service.accept(
            IncomingRequest(
                organization_id="empresa-demo",
                channel="telegram",
                external_id="msg-123",
                requested_by="user-42",
                message="Prepara el informe semanal",
                attachments=[],
            )
        )

        self.assertEqual(expedient.procedure_id, "prepare-report")
        self.assertEqual(expedient.procedure_version, "2.0")
        self.assertEqual(expedient.status, "awaiting_confirmation")
        self.assertEqual(expedient.timeline[0]["type"], "request_received")
        self.assertEqual(expedient.timeline[1]["type"], "procedure_proposed")

    def test_stops_when_the_proposer_selects_an_inactive_version(self):
        catalog = ProcedureCatalog()
        catalog.register(
            ProcedureDefinition(
                procedure_id="prepare-report",
                version="1.0",
                name="Preparar informe",
                description="Prepara un informe interno.",
                severity="low",
            )
        )
        catalog.activate("prepare-report", "1.0")
        service = IntakeService(
            catalog,
            FakeProposer(ProcedureProposal("prepare-report", "9.9", 0.99, "Versión no publicada.")),
        )

        with self.assertRaises(ValueError):
            service.accept(
                IncomingRequest(
                    organization_id="empresa-demo",
                    channel="email",
                    external_id="mail-123",
                    requested_by="sender@example.com",
                    message="Prepara el informe",
                    attachments=[],
                )
            )


if __name__ == "__main__":
    unittest.main()
