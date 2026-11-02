import tempfile
import unittest
from pathlib import Path

from fabrica.domain import Article, CampaignRequest
from fabrica.repositories import JsonWorkRepository
from fabrica.workflows import PrepareCampaignWorkflow


class FakeArticleReader:
    def read(self, path: Path) -> list[Article]:
        return [Article("Artículo", "Descripción", "https://example.com", "https://example.com/image.png")]


class PrepareCampaignWorkflowTests(unittest.TestCase):
    def test_prepares_campaign_and_blocks_sending(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonWorkRepository(Path(directory) / "work-items")
            workflow = PrepareCampaignWorkflow(FakeArticleReader(), repository)
            work = workflow.run(
                CampaignRequest(
                    subject="Novedades",
                    audience="clientes-españa",
                    scheduled_for=None,
                    source="test",
                    source_id="test-1",
                ),
                Path(directory) / "articles.xlsx",
            )

            self.assertEqual(work.status, "awaiting_approval")
            self.assertTrue(work.evidence["send_blocked"])
            self.assertEqual(work.evidence["article_count"], 1)

    def test_invalid_excel_is_recorded_as_failed_work(self):
        class FailingReader:
            def read(self, path: Path):
                raise ValueError("Faltan columnas obligatorias: ['url']")

        with tempfile.TemporaryDirectory() as directory:
            repository = JsonWorkRepository(Path(directory) / "work-items")
            workflow = PrepareCampaignWorkflow(FailingReader(), repository)
            work = workflow.run(
                CampaignRequest("Novedades", "clientes", None, "test", "test-2"),
                Path(directory) / "articles.xlsx",
            )

            self.assertEqual(work.status, "failed")
            self.assertEqual(len(work.errors), 1)


if __name__ == "__main__":
    unittest.main()
