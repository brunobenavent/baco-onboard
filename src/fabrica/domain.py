from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4


@dataclass(frozen=True)
class Article:
    title: str
    description: str
    url: str
    image_url: str


@dataclass(frozen=True)
class CampaignRequest:
    subject: str
    audience: str
    scheduled_for: Optional[str]
    source: str
    source_id: str


@dataclass
class Expedient:
    """Contexto durable y agnóstico de una petición de proceso."""

    procedure_id: str
    procedure_version: str
    organization_id: str
    channel: str
    requested_by: str
    inputs: dict[str, Any]
    status: str = "received"
    id: str = field(default_factory=lambda: f"exp-{uuid4().hex[:10]}")
    errors: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def start(
        cls,
        procedure_id: str,
        procedure_version: str,
        organization_id: str,
        channel: str,
        requested_by: str,
        inputs: dict[str, Any],
    ) -> "Expedient":
        return cls(
            procedure_id=procedure_id,
            procedure_version=procedure_version,
            organization_id=organization_id,
            channel=channel,
            requested_by=requested_by,
            inputs=inputs,
        )

    def record_event(self, event_type: str, data: dict[str, Any]) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        self.timeline.append({"at": timestamp, "type": event_type, "data": data})
        self.updated_at = timestamp

    def move_to(self, status: str) -> None:
        self.status = status
        self.record_event("status_changed", {"status": status})

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Expedient":
        return cls(**data)


@dataclass
class WorkItem:
    request: CampaignRequest
    status: str = "received"
    id: str = field(default_factory=lambda: f"work-{uuid4().hex[:10]}")
    errors: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkItem:
        request = CampaignRequest(**data.pop("request"))
        return cls(request=request, **data)
