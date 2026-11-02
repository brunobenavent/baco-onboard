import unittest

from fabrica.domain import Expedient, ProcedureDefinition
from fabrica.policy import PolicyEngine


class PolicyEngineTests(unittest.TestCase):
    def test_allows_procedures_at_or_below_the_automatic_threshold(self):
        engine = PolicyEngine(max_automatic_severity="medium")
        procedure = ProcedureDefinition(
            procedure_id="prepare-report",
            version="1.0",
            name="Preparar informe",
            description="Prepara un informe interno.",
            severity="medium",
        )

        decision = engine.evaluate(procedure)

        self.assertTrue(decision.allowed)
        self.assertFalse(decision.requires_human)
        self.assertEqual(decision.status, "ready_for_execution")

    def test_requires_human_for_a_severity_above_the_threshold(self):
        engine = PolicyEngine(max_automatic_severity="low")
        procedure = ProcedureDefinition(
            procedure_id="send-bulk-email",
            version="1.0",
            name="Enviar comunicación masiva",
            description="Envía una comunicación a una audiencia.",
            severity="high",
        )

        decision = engine.evaluate(procedure)

        self.assertTrue(decision.allowed)
        self.assertTrue(decision.requires_human)
        self.assertEqual(decision.status, "awaiting_approval")

    def test_blocks_unknown_severity(self):
        engine = PolicyEngine(max_automatic_severity="low")
        procedure = ProcedureDefinition(
            procedure_id="unclassified-process",
            version="1.0",
            name="Proceso sin clasificar",
            description="No tiene impacto conocido.",
            severity="unknown",
        )

        decision = engine.evaluate(procedure)

        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_human)
        self.assertEqual(decision.status, "blocked")

    def test_applies_the_decision_to_the_expedient(self):
        engine = PolicyEngine(max_automatic_severity="low")
        procedure = ProcedureDefinition(
            procedure_id="send-bulk-email",
            version="1.0",
            name="Enviar comunicación masiva",
            description="Envía una comunicación a una audiencia.",
            severity="high",
        )
        expedient = Expedient.start(
            procedure_id=procedure.procedure_id,
            procedure_version=procedure.version,
            organization_id="empresa-demo",
            channel="email",
            requested_by="operator-1",
            inputs={},
        )

        decision = engine.apply(expedient, procedure)

        self.assertEqual(decision.status, "awaiting_approval")
        self.assertEqual(expedient.status, "awaiting_approval")
        self.assertEqual(expedient.evidence["policy"]["severity"], "high")


if __name__ == "__main__":
    unittest.main()
