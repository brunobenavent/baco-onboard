from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol

from .domain import Article, CampaignRequest, WorkItem


class ArticleReader(Protocol):
    def read(self, path: Path) -> list[Article]: ...


class WorkRepository(Protocol):
    def save(self, work: WorkItem) -> None: ...

    def get(self, work_id: str) -> Optional[WorkItem]: ...


class CampaignSender(Protocol):
    def schedule(
        self, request: CampaignRequest, articles: list[Article]
    ) -> str: ...
