from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .domain import Expedient, WorkItem


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
