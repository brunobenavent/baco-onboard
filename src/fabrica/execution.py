from __future__ import annotations

from typing import Any, Optional, Protocol

from .domain import Expedient, ToolResult


class ToolExecutionError(Exception):
    def __init__(self, message: str, retriable: bool = False):
        super().__init__(message)
        self.retriable = retriable


class Tool(Protocol):
    def execute(
        self, operation: str, payload: dict[str, Any], idempotency_key: str
    ) -> dict[str, Any]: ...


class ExecutionLedger(Protocol):
    def save(self, idempotency_key: str, result: ToolResult) -> None: ...

    def get(self, idempotency_key: str) -> Optional[ToolResult]: ...


class InMemoryExecutionLedger:
    def __init__(self):
        self._results: dict[str, ToolResult] = {}

    def save(self, idempotency_key: str, result: ToolResult) -> None:
        self._results[idempotency_key] = result

    def get(self, idempotency_key: str) -> Optional[ToolResult]:
        return self._results.get(idempotency_key)


class ToolRegistry:
    """Resuelve nombres internos de herramientas sin acoplarse al proveedor."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, tool: Tool) -> None:
        if name in self._tools:
            raise ValueError(f"La herramienta ya está registrada: {name}")
        self._tools[name] = tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError as error:
            raise KeyError(f"Herramienta no registrada: {name}") from error


class ExecutionService:
    """Ejecuta herramientas solo después de la compuerta y evita duplicados."""

    def __init__(self, registry: ToolRegistry, ledger: Optional[ExecutionLedger] = None):
        self.registry = registry
        self.ledger = ledger or InMemoryExecutionLedger()

    def simulate(
        self,
        expedient: Expedient,
        tool_name: str,
        operation: str,
        payload: dict[str, Any],
    ) -> ToolResult:
        self.registry.get(tool_name)
        result = ToolResult(
            success=True,
            status="simulated",
            output={"tool": tool_name, "operation": operation, "payload": payload},
        )
        expedient.evidence["simulation"] = result.output
        expedient.record_event("simulation_completed", result.output)
        return result

    def execute(
        self,
        expedient: Expedient,
        tool_name: str,
        operation: str,
        payload: dict[str, Any],
        idempotency_key: str,
    ) -> ToolResult:
        if expedient.status != "ready_for_execution":
            raise ValueError("El expediente no está autorizado para ejecutar")

        previous = self.ledger.get(idempotency_key)
        if previous is not None:
            return ToolResult(
                success=previous.success,
                status="already_executed",
                output=previous.output,
                error=previous.error,
                retriable=previous.retriable,
            )

        tool = self.registry.get(tool_name)
        try:
            output = tool.execute(operation, payload, idempotency_key)
        except ToolExecutionError as error:
            status = "failed_retriable" if error.retriable else "failed"
            result = ToolResult(
                success=False,
                status=status,
                error=str(error),
                retriable=error.retriable,
            )
            self.ledger.save(idempotency_key, result)
            expedient.errors.append(str(error))
            expedient.record_event(
                "tool_failed",
                {
                    "tool": tool_name,
                    "operation": operation,
                    "idempotency_key": idempotency_key,
                    "retriable": error.retriable,
                    "error": str(error),
                },
            )
            expedient.move_to(status)
            return result

        result = ToolResult(success=True, status="executed", output=output)
        self.ledger.save(idempotency_key, result)
        expedient.evidence["execution"] = {
            "tool": tool_name,
            "operation": operation,
            "idempotency_key": idempotency_key,
            "output": output,
        }
        expedient.record_event("tool_executed", expedient.evidence["execution"])
        expedient.move_to("completed")
        return result
