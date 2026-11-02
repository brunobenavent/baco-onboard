from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

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

    def as_dict(self) -> dict:
        return {
            "definitions": [asdict(definition) for definition in self._definitions.values()],
            "active_versions": self._active_versions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProcedureCatalog":
        catalog = cls()
        for raw_definition in data.get("definitions", []):
            catalog.register(ProcedureDefinition(**raw_definition))
        catalog._active_versions.update(data.get("active_versions", {}))
        return catalog


class JsonProcedureCatalogRepository:
    """Persistencia de definiciones y versiones activas del catálogo."""

    def __init__(self, path: Path):
        self.path = path / "catalog.json" if path.is_dir() else path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, catalog: ProcedureCatalog) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(catalog.as_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def get(self) -> ProcedureCatalog:
        if not self.path.is_file():
            return ProcedureCatalog()
        return ProcedureCatalog.from_dict(json.loads(self.path.read_text(encoding="utf-8")))
