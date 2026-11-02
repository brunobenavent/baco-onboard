import tempfile
import unittest
from pathlib import Path

from fabrica.domain import Expedient
from fabrica.repositories import JsonExpedientRepository


class ExpedientTests(unittest.TestCase):
    def test_records_generic_process_without_knowing_a_vendor(self):
        expedient = Expedient.start(
            procedure_id="process-incoming-request",
            procedure_version="1.0",
            organization_id="empresa-demo",
            channel="telegram",
            requested_by="user-42",
            inputs={"message": "Preparar el informe semanal"},
        )

        expedient.record_event("request_received", {"channel": "telegram"})
        expedient.move_to("in_process")

        self.assertEqual(expedient.status, "in_process")
        self.assertEqual(expedient.procedure_id, "process-incoming-request")
        self.assertEqual(expedient.timeline[0]["type"], "request_received")

    def test_repository_round_trip_preserves_identity_and_timeline(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonExpedientRepository(Path(directory))
            original = Expedient.start(
                procedure_id="prepare-report",
                procedure_version="2.1",
                organization_id="empresa-demo",
                channel="scheduler",
                requested_by="scheduler",
                inputs={"period": "2026-W45"},
            )
            original.record_event("scheduled", {"period": "2026-W45"})
            repository.save(original)

            restored = repository.get(original.id)

            self.assertIsNotNone(restored)
            self.assertEqual(restored.procedure_version, "2.1")
            self.assertEqual(restored.organization_id, "empresa-demo")
            self.assertEqual(restored.timeline[0]["type"], "scheduled")


if __name__ == "__main__":
    unittest.main()
