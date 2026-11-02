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

## Cómo se usa

### 1. Instalar la fábrica

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/baco --help
```

### 2. Comandos de la fábrica

Iniciar el procedimiento de resumen de PDF:

```bash
.venv/bin/baco run summarize-pdf-email \
  --sender brunobenavent@gmail.com \
  --telegram @mi_usuario
```

El usuario solo proporciona los datos propios del proceso:

| Entrada | Ejemplo | Significado |
| --- | --- | --- |
| `summarize-pdf-email` | nombre del proceso | Procedimiento que se quiere iniciar |
| `--sender` | `brunobenavent@gmail.com` | Remitente permitido |
| `--telegram` | `@mi_usuario` | Destinatario del resumen |

La fábrica decide internamente la versión, severidad, organización por defecto,
carpeta de estado y formato del expediente.

Consultar o resolver el expediente cuando sea necesario:

```bash
.venv/bin/baco status --id EXPEDIENT_ID --state-dir .baco/state
.venv/bin/baco approve --id EXPEDIENT_ID --by operador-1 --comment "Revisado" --state-dir .baco/state
.venv/bin/baco reject --id EXPEDIENT_ID --by operador-1 --comment "Falta revisar el PDF" --state-dir .baco/state
.venv/bin/baco expire --id EXPEDIENT_ID --state-dir .baco/state
```

`baco run <procedimiento>` es la entrada equivalente a un `superboard run`:
selecciona un procedimiento por nombre y aplica su definición interna.
`baco intake` y el modo técnico de `baco run` quedan para integradores y
diagnóstico, no para el uso diario.

### Modo técnico

Cuando se está desarrollando un procedimiento nuevo, se puede iniciar con todos
los metadatos explícitos. Este modo no es necesario para ejecutar un proceso ya
registrado:

```bash
.venv/bin/baco intake \
  --message "Resume el PDF adjunto" \
  --channel email \
  --organization empresa-demo \
  --requested-by brunobenavent@gmail.com \
  --external-id mail-001 \
  --procedure-id summarize-pdf-email \
  --procedure-version 1.0 \
  --severity low \
  --state-dir .baco/state \
  --output .baco/expedient.json
```

### 3. Proceso de campaña desde Excel

El comando `prepare` mantiene el primer prototipo:

```bash
.venv/bin/baco prepare \
  --request request.example.json \
  --articles articulos.example.xlsx \
  --output campaign-draft.json
```

El JSON debe tener:

```json
{
  "subject": "Novedades",
  "audience": "clientes-españa",
  "scheduled_for": null,
  "source": "email",
  "source_id": "mail-001"
}
```

El Excel debe contener las columnas:

```text
title, description, url, image_url
```

### 4. Proceso email → PDF → resumen → Telegram

El procedimiento `summarize-pdf-email` espera conceptualmente:

```text
canal: email
remitente permitido: brunobenavent@gmail.com
adjuntos: exactamente un PDF
destino: destinatario de Telegram
```

Su recorrido es:

```text
EmailMessage
  → validar remitente
  → localizar un PDF
  → extraer texto con PypdfTextExtractor
  → resumir con Summarizer
  → enviar mediante TelegramMessenger
```

El procedimiento y sus adapters ya tienen pruebas falsas de extremo a
extremo. Gmail y Telegram todavía deben registrarse en el entorno de ejecución.

Para probarlo sin conectores de pago, copia el ejemplo junto a un PDF real y
ejecuta:

```bash
cp examples/email.example.json /tmp/email.json
# coloca el PDF como /tmp/documento.pdf y actualiza el path del JSON si hace falta
.venv/bin/baco run summarize-pdf-email \
  --email-file /tmp/email.json \
  --outbox .baco/telegram-outbox
```

En este modo el correo se lee desde JSON y el “Telegram” se simula escribiendo
un fichero de texto en `.baco/telegram-outbox/`. El procedimiento, el PDF y el
resumen son reales; solo se sustituyen los dos extremos externos.

### 5. Estados posibles

```text
received              entrada recibida
awaiting_confirmation propuesta pendiente de confirmación
awaiting_approval     necesita aprobación humana
ready_for_execution   autorizado para ejecutar
completed             terminado correctamente
changes_requested     devuelto para cambios
rejected              rechazado
approval_expired      aprobación caducada
failed                error no retriable
failed_retriable      error que puede reintentarse
blocked               bloqueado por política
```

## Contratos importantes

- `WorkRepository` conserva trabajos y permite sustituir JSON por SQLite,
  PostgreSQL u otro servicio.
- `ArticleReader` permite sustituir Excel por CSV, Google Sheets o un adjunto.
- `PdfTextExtractor` extrae texto sin decidir cómo se resume.
- `Summarizer` permite conectar un agente, un modelo o un resumidor local.
- `Messenger` permite conectar Telegram, WhatsApp, email u otro canal.
- `ToolRegistry` y `ExecutionService` ejecutan adapters con simulación,
  idempotencia y evidencia.
