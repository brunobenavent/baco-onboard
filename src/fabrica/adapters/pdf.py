from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


class PypdfTextExtractor:
    """Extrae texto de un PDF sin decidir cómo debe resumirse."""

    def extract(self, path: Path) -> str:
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(page.strip() for page in pages if page.strip())
