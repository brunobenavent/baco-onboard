from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from ..domain import Article


class ExcelArticleReader:
    required_columns = {"title", "description", "url", "image_url"}

    def read(self, path: Path) -> list[Article]:
        workbook = load_workbook(path, read_only=True, data_only=True)
        sheet = workbook.active
        rows = sheet.iter_rows(values_only=True)
        headers = [str(value or "").strip().lower() for value in next(rows, ())]
        missing = self.required_columns - set(headers)
        if missing:
            raise ValueError(f"Faltan columnas obligatorias: {sorted(missing)}")

        index = {header: position for position, header in enumerate(headers)}
        articles: list[Article] = []
        for row_number, row in enumerate(rows, start=2):
            values = {
                column: str(row[index[column]] or "").strip()
                for column in self.required_columns
            }
            if not any(values.values()):
                continue
            empty = [column for column, value in values.items() if not value]
            if empty:
                raise ValueError(
                    f"Fila {row_number}: campos vacíos: {', '.join(sorted(empty))}"
                )
            articles.append(Article(**values))
        return articles
