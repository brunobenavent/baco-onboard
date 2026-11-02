# BACO Onboard — fábrica de automatización de procesos

BACO Onboard convierte peticiones y documentos en procesos ejecutables con
validación, aprobación y evidencia. Su primer proceso prepara una campaña a
partir de un Excel; después añadiremos lectura de emails, albaranes y Sage.

La definición de dominio está en [GLOSSARY.md](GLOSSARY.md), la decisión
arquitectónica en [docs/adr/0001-agnostic-process-core.md](docs/adr/0001-agnostic-process-core.md)
y el diseño ampliado en [docs/architecture.md](docs/architecture.md).

El núcleo ya incluye un expediente durable y un catálogo versionado de
procedimientos. El catálogo no conoce proveedores externos: cada procedimiento
declara su severidad, si requiere aprobación y si admite simulación.

La entrada se normaliza mediante `IntakeService`. Su proponente es sustituible:
puede ser código determinista, un agente o un servicio externo. La petición
queda registrada en el expediente antes de cualquier acción externa.

`PolicyEngine` aplica el umbral de severidad de la organización: los procesos
que lo superan esperan aprobación humana y los que no tienen severidad válida
quedan bloqueados.

La decisión humana se gestiona mediante `ApprovalService`, que permite aprobar,
rechazar o solicitar cambios y deja la decisión en la evidencia del expediente.
También admite fechas límite para que una aprobación antigua caduque antes de
ejecutar una acción.

Los resultados pueden notificarse mediante `NotificationService`, que usa un
adapter por canal y registra cada notificación en la línea temporal.

`ProcessRuntime` ofrece el recorrido compuesto de recepción, propuesta,
política y persistencia del expediente.

El primer procedimiento de prueba es `SummarizePdfEmailProcess`: acepta un
email de `brunobenavent@gmail.com` con un único PDF, extrae su texto mediante
`PypdfTextExtractor`, lo entrega a un `Summarizer` y envía el resultado mediante
un adapter de Telegram.

## Mapa de la fábrica

Abre [diagrams/factory-map.html](diagrams/factory-map.html) para explorar la
arquitectura. Se regenera desde `diagrams/factory-map.json` con:

```bash
python3 scripts/build_map.py
```

## Recorrido

```text
request.json + articulos.xlsx
        ↓
PrepareCampaignWorkflow
        ↓
ExcelArticleReader
        ↓
validación de artículos
        ↓
campaign-draft.json
        ↓
aprobación humana (siguiente fase)
        ↓
MailchimpCampaignSender (siguiente fase)
```

El workflow no conoce GitHub, un chat ni Mailchimp. Esas piezas son adapters
que traducen entradas y salidas externas al modelo interno de la fábrica.

## Ejecutar

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m fabrica.cli prepare \
  --request request.example.json \
  --articles articulos.example.xlsx \
  --output campaign-draft.json
```

## Comandos de la fábrica

Después de instalar el proyecto, el comando principal es `baco`:

```bash
baco --help
```

Iniciar un proceso y crear su expediente:

```bash
baco run \
  --message "Resume el PDF adjunto" \
  --channel email \
  --organization empresa-demo \
  --requested-by brunobenavent@gmail.com \
  --external-id mail-001 \
  --procedure-id summarize-pdf-email \
  --procedure-version 1.0 \
  --severity low \
  --state-dir .baco/state \
  --output .baco/expedients/expedient.json
```

Consultar o resolver el expediente:

```bash
baco status --id EXPEDIENT_ID --state-dir .baco/state
baco approve --id EXPEDIENT_ID --by operador-1 --state-dir .baco/state
baco reject --id EXPEDIENT_ID --by operador-1 --comment "Falta revisar el PDF" --state-dir .baco/state
baco expire --id EXPEDIENT_ID --state-dir .baco/state
```

`baco run` es la entrada equivalente a un `superboard run`: inicia un proceso
con una definición y versión concretas. La CLI todavía no conecta Gmail ni
Telegram por sí sola; esos adapters se registran cuando se configura cada
entorno.

Para usarlo con tus propios datos, el Excel debe tener estas columnas:

```text
title, description, url, image_url
```

## Contratos importantes

- `WorkRepository` conserva el trabajo y permite sustituir JSON por SQLite,
  PostgreSQL o un servicio externo.
- `ArticleReader` permite sustituir Excel por CSV, Google Sheets o un adjunto
  recibido desde un chat.
- `CampaignSender` permite sustituir el envío simulado por Mailchimp, Brevo o
  un proveedor interno.
- El workflow solo prepara y valida. El envío queda fuera hasta añadir una
  aprobación explícita.
