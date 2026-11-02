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
