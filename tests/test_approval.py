import unittest

from fabrica.approval import ApprovalService
from fabrica.domain import Expedient


def pending_expedient():
    expedient = Expedient.start(
        procedure_id="send-bulk-email",
        procedure_version="1.0",
        organization_id="empresa-demo",
        channel="telegram",
        requested_by="user-42",
        inputs={"audience": "clientes"},
    )
    expedient.move_to("awaiting_approval")
    return expedient


class ApprovalServiceTests(unittest.TestCase):
    def test_approves_and_records_the_human_decision(self):
        expedient = pending_expedient()

        ApprovalService().approve(expedient, "manager-7", "Revisado y aprobado")

        self.assertEqual(expedient.status, "ready_for_execution")
        self.assertEqual(expedient.evidence["approval"]["decided_by"], "manager-7")
        self.assertEqual(expedient.timeline[-1]["type"], "approval_granted")

    def test_rejects_the_expedient(self):
        expedient = pending_expedient()

        ApprovalService().reject(expedient, "manager-7", "La audiencia no es correcta")

        self.assertEqual(expedient.status, "rejected")
        self.assertEqual(expedient.timeline[-1]["type"], "approval_rejected")

    def test_requests_changes(self):
        expedient = pending_expedient()

        ApprovalService().request_changes(expedient, "manager-7", "Añadir el enlace al informe")

        self.assertEqual(expedient.status, "changes_requested")
        self.assertEqual(expedient.timeline[-1]["type"], "changes_requested")

    def test_cannot_decide_when_approval_is_not_pending(self):
        expedient = pending_expedient()
        ApprovalService().approve(expedient, "manager-7")

        with self.assertRaises(ValueError):
            ApprovalService().reject(expedient, "manager-8")


if __name__ == "__main__":
    unittest.main()
