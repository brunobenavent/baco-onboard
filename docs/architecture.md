# Arquitectura de BACO Onboard

```text
WhatsApp / Telegram / Email / Scheduler
                    ↓
              Intake adapters
                    ↓
             Petición normalizada
                    ↓
              Expediente durable
                    ↓
       Catálogo de procedimientos + agente
                    ↓
        Política, severidad y simulación
             ↙          ↓          ↘
   información       aprobación    herramientas
    pendiente        humana        externas
                                      ↓
                         MCP / API / SDK / CLI adapters
                    ↓
          resultado + evidencia + notificación
```

El catálogo mantiene la definición de cada procedimiento por `procedure_id` y
versión. Una versión solo puede utilizarse como versión activa después de ser
registrada y activada explícitamente; los expedientes ya creados conservan la
versión con la que comenzaron.

`IntakeService` recibe la petición normalizada y delega la propuesta a un
`ProcedureProposer`. El proponente puede ser una regla, un agente o un servicio
externo; el núcleo solo exige que devuelva un procedimiento y una versión. La
petición queda en `awaiting_confirmation` hasta que la política determine el
siguiente paso.

`PolicyEngine` compara la severidad del procedimiento con el umbral automático
de la organización. Puede dejar el expediente listo para ejecución, enviarlo a
`awaiting_approval` o bloquearlo cuando la severidad no está clasificada.

`ApprovalService` resuelve la intervención humana con tres decisiones posibles:
aprobar, rechazar o solicitar cambios. Cada decisión registra identidad,
comentario, estado y evento en la línea temporal del expediente.
Las aprobaciones pueden tener una fecha límite; al caducar pasan a
`approval_expired` y dejan de poder resolverse.

`NotificationService` publica el resultado por el canal de origen mediante un
adapter registrado. El núcleo no sabe si ese adapter termina en Telegram,
WhatsApp, email u otro canal.

`ProcessRuntime` compone las piezas del núcleo para el recorrido inicial:
recibe la petición, crea el expediente, resuelve el procedimiento, aplica la
política y persiste el estado antes de cualquier ejecución externa.

El procedimiento de prueba email-PDF-resumen-Telegram separa tres adapters:
lector de email, extractor de PDF y resumidor. Así podemos cambiar Gmail por
otro buzón, `pypdf` por otro extractor o el modelo de resumen sin cambiar el
procedimiento.

Telegram también funciona como entrada conversacional: el receptor valida el
chat autorizado, mantiene el estado del diálogo y convierte la idea del usuario
en una propuesta de procedimiento antes de activarla.

## Módulos del núcleo

- **Expediente**: fuente de verdad de la ejecución de BACO: entradas, estado,
  versión, decisiones, acciones y línea temporal.
- **Catálogo de procedimientos**: procedimientos versionados, con propietario,
  política, severidad, entradas, salidas y errores declarados.
- **Agente**: interpreta la petición, propone procedimientos y coordina pasos
  permitidos; no sustituye las políticas.
- **Policy engine**: calcula el nivel de intervención y aplica roles,
  permisos, caducidad y aprobación.
- **Tool contract**: interfaz común para cualquier herramienta externa. MCP es
  una posible implementación de ese contrato.
- **Evidence log**: conserva qué ocurrió, cuándo, con qué identidad y bajo qué
  versión del procedimiento.

## Primeros procedimientos de prueba

1. Leer y clasificar una petición recibida por email.
2. Preparar una comunicación externa con aprobación.
3. Ejecutar una recopilación programada y generar un informe.

Procesar albaranes, consultar Sage y enviar campañas serán adapters o
procedimientos posteriores; no forman parte del núcleo agnóstico.
