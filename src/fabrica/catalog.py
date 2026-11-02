from __future__ import annotations

from .domain import ProcedureDefinition


class ProcedureCatalog:
    """Catálogo en memoria para registrar y seleccionar procedimientos."""

    def __init__(self):
        self._definitions: dict[tuple[str, str], ProcedureDefinition] = {}
        self._active_versions: dict[str, str] = {}

    def register(self, definition: ProcedureDefinition) -> None:
        key = (definition.procedure_id, definition.version)
        if key in self._definitions:
            raise ValueError(
                f"El procedimiento ya está registrado: {definition.procedure_id}@{definition.version}"
            )
        self._definitions[key] = definition

    def activate(self, procedure_id: str, version: str) -> None:
        if (procedure_id, version) not in self._definitions:
            raise KeyError(f"Procedimiento no registrado: {procedure_id}@{version}")
        self._active_versions[procedure_id] = version

    def get(self, procedure_id: str, version: str) -> ProcedureDefinition:
        try:
            return self._definitions[(procedure_id, version)]
        except KeyError as error:
            raise KeyError(f"Procedimiento no registrado: {procedure_id}@{version}") from error

    def get_active(self, procedure_id: str) -> ProcedureDefinition:
        try:
            version = self._active_versions[procedure_id]
        except KeyError as error:
            raise KeyError(f"No hay versión activa para: {procedure_id}") from error
        return self.get(procedure_id, version)
