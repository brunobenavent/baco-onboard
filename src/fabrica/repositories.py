from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Optional

from .catalog import JsonProcedureCatalogRepository
from .domain import Expedient, ToolResult, WorkItem


class JsonExecutionRepository:
    """Ledger durable de resultados indexado por clave de idempotencia."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path_for(self, idempotency_key: str) -> Path:
        digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
        return self.directory / f"{digest}.json"

    def save(self, idempotency_key: str, result: ToolResult) -> None:
        destination = self._path_for(idempotency_key)
        temporary = destination.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(result.as_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(destination)

    def get(self, idempotency_key: str) -> Optional[ToolResult]:
        path = self._path_for(idempotency_key)
        if not path.is_file():
            return None
        return ToolResult(**json.loads(path.read_text(encoding="utf-8")))


class JsonExpedientRepository:
    """Persistencia local del expediente, independiente del procedimiento."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, expedient: Expedient) -> None:
        destination = self.directory / f"{expedient.id}.json"
        temporary = destination.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(expedient.as_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(destination)

    def get(self, expedient_id: str) -> Optional[Expedient]:
        path = self.directory / f"{expedient_id}.json"
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return Expedient.from_dict(data)


class JsonWorkRepository:
    """Implementación pequeña y legible del repositorio de trabajos."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, work: WorkItem) -> None:
        destination = self.directory / f"{work.id}.json"
        temporary = destination.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(work.as_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(destination)

    def get(self, work_id: str) -> Optional[WorkItem]:
        path = self.directory / f"{work_id}.json"
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return WorkItem.from_dict(data)
