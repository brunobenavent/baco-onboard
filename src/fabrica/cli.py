from __future__ import annotations

import argparse
import json
from pathlib import Path

from .approval import ApprovalService
from .catalog import ProcedureCatalog
from .domain import CampaignRequest, IncomingRequest, ProcedureDefinition, ProcedureProposal
from .intake import IntakeService
from .policy import PolicyEngine
from .repositories import JsonExpedientRepository, JsonWorkRepository
from .runtime import ProcessRuntime
from .workflows import PrepareCampaignWorkflow


class CommandLineProposer:
    """Proponente explícito para CLI; un agente podrá sustituirlo después."""

    def __init__(self, proposal: ProcedureProposal):
        self.proposal = proposal

    def propose(self, request: IncomingRequest) -> ProcedureProposal:
        return self.proposal


def _add_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--message", required=True)
    parser.add_argument("--channel", required=True)
    parser.add_argument("--organization", required=True)
    parser.add_argument("--requested-by", required=True)
    parser.add_argument("--external-id", required=True)
    parser.add_argument("--procedure-id", required=True)
    parser.add_argument("--procedure-version", required=True)
    parser.add_argument("--severity", required=True)
    parser.add_argument("--max-automatic-severity", default="low")
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)


def _run_process(args: argparse.Namespace) -> int:
    catalog = ProcedureCatalog()
    catalog.register(
        ProcedureDefinition(
            procedure_id=args.procedure_id,
            version=args.procedure_version,
            name=args.procedure_id,
            description="Procedimiento iniciado desde la CLI",
            severity=args.severity,
        )
    )
    catalog.activate(args.procedure_id, args.procedure_version)
    proposal = ProcedureProposal(
        args.procedure_id,
        args.procedure_version,
        1.0,
        "Procedimiento indicado explícitamente por la CLI",
    )
    runtime = ProcessRuntime(
        IntakeService(catalog, CommandLineProposer(proposal)),
        catalog,
        PolicyEngine(args.max_automatic_severity),
        JsonExpedientRepository(args.state_dir),
    )
    expedient = runtime.receive(
        IncomingRequest(
            organization_id=args.organization,
            channel=args.channel,
            external_id=args.external_id,
            requested_by=args.requested_by,
            message=args.message,
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(expedient.as_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(expedient.as_dict(), indent=2, ensure_ascii=False))
    return 0 if expedient.status in {"ready_for_execution", "awaiting_approval"} else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="BACO: fábrica agnóstica de procesos")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="inicia un proceso y crea su expediente")
    _add_run_arguments(run)
    intake = subparsers.add_parser("intake", help="registra una entrada de proceso")
    _add_run_arguments(intake)

    approve = subparsers.add_parser("approve", help="aprueba un expediente pendiente")
    approve.add_argument("--id", required=True)
    approve.add_argument("--by", required=True)
    approve.add_argument("--comment", default="")
    approve.add_argument("--state-dir", type=Path, required=True)

    reject = subparsers.add_parser("reject", help="rechaza un expediente pendiente")
    reject.add_argument("--id", required=True)
    reject.add_argument("--by", required=True)
    reject.add_argument("--comment", default="")
    reject.add_argument("--state-dir", type=Path, required=True)

    status = subparsers.add_parser("status", help="muestra un expediente")
    status.add_argument("--id", required=True)
    status.add_argument("--state-dir", type=Path, required=True)

    expire = subparsers.add_parser("expire", help="caduca una aprobación vencida")
    expire.add_argument("--id", required=True)
    expire.add_argument("--state-dir", type=Path, required=True)

    prepare = subparsers.add_parser("prepare", help="prepara una campaña desde Excel")
    prepare.add_argument("--request", type=Path, required=True)
    prepare.add_argument("--articles", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command in {"run", "intake"}:
        return _run_process(args)

    if args.command in {"approve", "reject", "expire", "status"}:
        repository = JsonExpedientRepository(args.state_dir)
        expedient = repository.get(args.id)
        if expedient is None:
            print(f"No existe el expediente: {args.id}")
            return 1
        if args.command == "approve":
            ApprovalService().approve(expedient, args.by, args.comment)
        elif args.command == "reject":
            ApprovalService().reject(expedient, args.by, args.comment)
        elif args.command == "expire":
            ApprovalService().expire_if_due(expedient)
        repository.save(expedient)
        print(json.dumps(expedient.as_dict(), indent=2, ensure_ascii=False))
        return 0

    if args.command == "prepare":
        from .adapters.excel import ExcelArticleReader

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
