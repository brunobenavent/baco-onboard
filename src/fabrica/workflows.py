from __future__ import annotations

from pathlib import Path

from .domain import CampaignRequest, WorkItem
from .ports import ArticleReader, WorkRepository


class PrepareCampaignWorkflow:
    """Skill de preparación: devuelve un borrador, nunca envía una campaña."""

    def __init__(self, article_reader: ArticleReader, work_repository: WorkRepository):
        self.article_reader = article_reader
        self.work_repository = work_repository

    def run(self, request: CampaignRequest, articles_path: Path) -> WorkItem:
        work = WorkItem(request=request, status="parsing")
        try:
            articles = self.article_reader.read(articles_path)
            if not articles:
                raise ValueError("El Excel no contiene artículos")
            work.status = "awaiting_approval"
            work.evidence = {
                "articles_path": str(articles_path),
                "article_count": len(articles),
                "preview": [article.__dict__ for article in articles[:3]],
                "send_blocked": True,
            }
        except (OSError, ValueError) as error:
            work.status = "failed"
            work.errors.append(str(error))
        self.work_repository.save(work)
        return work
