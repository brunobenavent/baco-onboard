import unittest
import tempfile
from pathlib import Path

from fabrica.domain import Expedient
from fabrica.execution import ExecutionService, ToolExecutionError, ToolRegistry
from fabrica.repositories import JsonExecutionRepository


class FakeTool:
    def __init__(self):
        self.calls = []

    def execute(self, operation, payload, idempotency_key):
        self.calls.append((operation, payload, idempotency_key))
        return {"remote_id": "remote-123", "operation": operation}


class FailingTool:
    def __init__(self, retriable):
        self.retriable = retriable

    def execute(self, operation, payload, idempotency_key):
        raise ToolExecutionError("Servicio temporalmente no disponible", self.retriable)


def executable_expedient():
    expedient = Expedient.start(
        procedure_id="prepare-report",
        procedure_version="1.0",
        organization_id="empresa-demo",
        channel="email",
        requested_by="user-42",
        inputs={"period": "2026-W45"},
    )
    expedient.move_to("ready_for_execution")
    return expedient


class ExecutionServiceTests(unittest.TestCase):
    def test_simulation_does_not_call_the_external_tool(self):
        tool = FakeTool()
        registry = ToolRegistry()
        registry.register("reporting", tool)
        service = ExecutionService(registry)
        expedient = executable_expedient()

        result = service.simulate(expedient, "reporting", "create", {"period": "2026-W45"})

        self.assertTrue(result.success)
        self.assertEqual(result.status, "simulated")
        self.assertEqual(tool.calls, [])
        self.assertEqual(expedient.timeline[-1]["type"], "simulation_completed")

    def test_executes_and_records_the_external_result(self):
        tool = FakeTool()
        registry = ToolRegistry()
        registry.register("reporting", tool)
        service = ExecutionService(registry)
        expedient = executable_expedient()

        result = service.execute(
            expedient,
            "reporting",
            "create",
            {"period": "2026-W45"},
            idempotency_key="exp-1-report",
        )

        self.assertTrue(result.success)
        self.assertEqual(expedient.status, "completed")
        self.assertEqual(result.output["remote_id"], "remote-123")
        self.assertEqual(len(tool.calls), 1)

    def test_idempotency_prevents_duplicate_external_actions(self):
        tool = FakeTool()
        registry = ToolRegistry()
        registry.register("reporting", tool)
        service = ExecutionService(registry)
        first = executable_expedient()
        second = executable_expedient()

        service.execute(first, "reporting", "create", {}, idempotency_key="same-key")
        duplicate = service.execute(second, "reporting", "create", {}, idempotency_key="same-key")

        self.assertTrue(duplicate.success)
        self.assertEqual(duplicate.status, "already_executed")
        self.assertEqual(len(tool.calls), 1)

    def test_execution_requires_an_approved_expedient(self):
        tool = FakeTool()
        registry = ToolRegistry()
        registry.register("reporting", tool)
        service = ExecutionService(registry)
        expedient = Expedient.start("prepare-report", "1.0", "empresa-demo", "email", "user-42", {})

        with self.assertRaises(ValueError):
            service.execute(expedient, "reporting", "create", {}, idempotency_key="blocked")

    def test_persistent_ledger_prevents_duplicates_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            tool = FakeTool()
            registry = ToolRegistry()
            registry.register("reporting", tool)
            ledger = JsonExecutionRepository(Path(directory))
            first_service = ExecutionService(registry, ledger)
            first_service.execute(
                executable_expedient(), "reporting", "create", {}, idempotency_key="durable-key"
            )

            restarted_service = ExecutionService(registry, JsonExecutionRepository(Path(directory)))
            duplicate = restarted_service.execute(
                executable_expedient(), "reporting", "create", {}, idempotency_key="durable-key"
            )

            self.assertEqual(duplicate.status, "already_executed")
            self.assertEqual(len(tool.calls), 1)

    def test_records_a_retriable_tool_failure(self):
        registry = ToolRegistry()
        registry.register("reporting", FailingTool(retriable=True))
        service = ExecutionService(registry)
        expedient = executable_expedient()

        result = service.execute(expedient, "reporting", "create", {}, idempotency_key="retry-key")

        self.assertFalse(result.success)
        self.assertTrue(result.retriable)
        self.assertEqual(result.status, "failed_retriable")
        self.assertEqual(expedient.status, "failed_retriable")

    def test_records_a_non_retriable_tool_failure(self):
        registry = ToolRegistry()
        registry.register("reporting", FailingTool(retriable=False))
        service = ExecutionService(registry)
        expedient = executable_expedient()

        result = service.execute(expedient, "reporting", "create", {}, idempotency_key="invalid-key")

        self.assertFalse(result.success)
        self.assertFalse(result.retriable)
        self.assertEqual(result.status, "failed")
        self.assertEqual(expedient.status, "failed")


if __name__ == "__main__":
    unittest.main()
