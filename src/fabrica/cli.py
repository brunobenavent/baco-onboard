from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import uuid4

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


def _add_run_arguments(parser: argparse.ArgumentParser, required: bool = True) -> None:
    parser.add_argument("--message", required=required)
    parser.add_argument("--channel", required=required)
    parser.add_argument("--organization", required=required)
    parser.add_argument("--requested-by", required=required)
    parser.add_argument("--external-id", required=required)
    parser.add_argument("--procedure-id", required=required)
    parser.add_argument("--procedure-version", required=required)
    parser.add_argument("--severity", required=required)
    parser.add_argument("--max-automatic-severity", default="low")
    parser.add_argument("--state-dir", type=Path, required=required, default=Path(".baco/state"))
    parser.add_argument("--output", type=Path, required=required)


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
            metadata=getattr(args, "metadata", {}),
        )
    )
    output = args.output or Path(".baco/expedients") / f"{expedient.id}.json"
    args.output = output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(expedient.as_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(expedient.as_dict(), indent=2, ensure_ascii=False))
    return 0 if expedient.status in {"ready_for_execution", "awaiting_approval"} else 1


def _run_named_process(args: argparse.Namespace) -> int:
    if args.procedure != "summarize-pdf-email":
        print(f"Procedimiento no conocido: {args.procedure}")
        return 1
    local_message = None
    if args.pdf:
        from .email_process import EmailAttachment, EmailMessage

        local_message = EmailMessage(
            message_id=f"local-{uuid4().hex[:10]}",
            sender=args.sender or "",
            subject=args.subject,
            attachments=[EmailAttachment(args.pdf.name, args.pdf, "application/pdf")],
        )
        args.sender = args.sender or local_message.sender
        args.telegram = args.telegram or "local-telegram"
    elif args.email_file:
        from .adapters.local import LocalJsonEmailReader

        local_message = LocalJsonEmailReader().read(args.email_file)
        args.sender = args.sender or local_message.sender
        args.telegram = args.telegram or "local-telegram"
    elif not args.sender or not args.telegram:
        print("summarize-pdf-email requiere --sender y --telegram")
        return 2

    args.message = f"Resumir los PDFs recibidos de {args.sender} y enviar el resultado por Telegram"
    args.channel = "email"
    args.organization = "personal"
    args.requested_by = args.sender
    args.external_id = "manual-run"
    args.procedure_id = "summarize-pdf-email"
    args.procedure_version = "1.0"
    args.severity = "low"
    args.metadata = {"telegram_recipient": args.telegram}
    exit_code = _run_process(args)
    if exit_code != 0 or local_message is None:
        return exit_code

    from .adapters.local import FileMessenger, SimpleSummarizer
    from .adapters.pdf import PypdfTextExtractor
    from .email_process import SummarizePdfEmailProcess

    delivery = SummarizePdfEmailProcess(
        PypdfTextExtractor(),
        SimpleSummarizer(),
        FileMessenger(args.outbox),
        args.sender,
    ).run(local_message, args.telegram)
    repository = JsonExpedientRepository(args.state_dir)
    expedient = repository.get(json.loads(args.output.read_text(encoding="utf-8"))["id"])
    if expedient is None:
        return 1
    expedient.evidence["delivery"] = {
        "status": delivery.status,
        "summary": delivery.summary,
        "notification_id": delivery.notification_id,
    }
    expedient.move_to("completed")
    repository.save(expedient)
    args.output.write_text(
        json.dumps(expedient.as_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(expedient.as_dict(), indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="BACO: fábrica agnóstica de procesos")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="inicia un proceso por nombre")
    run.add_argument("procedure", nargs="?")
    run.add_argument("--sender")
    run.add_argument("--telegram")
    run.add_argument("--email-file", type=Path)
    run.add_argument("--pdf", type=Path)
    run.add_argument("--subject", default="Documento para resumir")
    run.add_argument("--outbox", type=Path, default=Path(".baco/telegram-outbox"))
    _add_run_arguments(run, required=False)
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

    if args.command == "run" and args.procedure:
        return _run_named_process(args)

    if args.command in {"run", "intake"}:
        required_fields = [
            "message", "channel", "organization", "requested_by", "external_id",
            "procedure_id", "procedure_version", "severity", "output",
        ]
        missing = [field for field in required_fields if getattr(args, field, None) is None]
        if missing:
            parser.error(f"run técnico requiere: {', '.join('--' + field.replace('_', '-') for field in missing)}")
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
