from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters.excel import ExcelArticleReader
from .domain import CampaignRequest
from .repositories import JsonWorkRepository
from .workflows import PrepareCampaignWorkflow


def main() -> int:
    parser = argparse.ArgumentParser(description="Fábrica agnóstica de procesos")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare", help="prepara una campaña desde Excel")
    prepare.add_argument("--request", type=Path, required=True)
    prepare.add_argument("--articles", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "prepare":
        data = json.loads(args.request.read_text(encoding="utf-8"))
        request = CampaignRequest(**data)
        repository = JsonWorkRepository(args.output.parent / ".work-items")
        work = PrepareCampaignWorkflow(ExcelArticleReader(), repository).run(
            request, args.articles
        )
        args.output.write_text(
            json.dumps(work.as_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(work.as_dict(), indent=2, ensure_ascii=False))
        return 0 if work.status == "awaiting_approval" else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
