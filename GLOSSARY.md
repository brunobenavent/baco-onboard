# Glosario de BACO Onboard

## Fábrica de automatización de procesos

Sistema que convierte una petición o un evento empresarial en una operación
ejecutada y registrada.

## Expediente

Unidad de trabajo independiente que conserva la entrada, el contexto, el
estado, las decisiones, las acciones realizadas y el resultado de una
ejecución.

## Procedimiento

Descripción versionada de lo que la empresa quiere conseguir y de los pasos,
validaciones, políticas y puntos de aprobación que deben aplicarse. No depende
de una herramienta concreta.

## Herramienta

Sistema externo o capacidad técnica utilizada por un procedimiento para actuar
o consultar información. Puede sustituirse sin cambiar el objetivo del
procedimiento.

## Agente

Coordinador que interpreta el contexto y decide el siguiente paso permitido
dentro de un procedimiento. No es, por sí mismo, la autoridad para ejecutar
cualquier operación.

## Severidad

Nivel de impacto de una acción sobre la empresa. La severidad determina si una
acción puede ejecutarse automáticamente o requiere que una persona intervenga.

## Intervención humana

Punto explícito del procedimiento en el que una persona debe aprobar, rechazar,
corregir o completar información antes de continuar.

## Resultado

Estado y evidencia final de un expediente: qué se intentó, qué ocurrió, qué
quedó pendiente y qué debe suceder después.

## Canal de entrada

Medio por el que una persona, sistema o evento entrega información a la
fábrica. El canal no determina el procedimiento: solo crea o alimenta un
expediente.

Los canales iniciales de BACO Onboard son conversación —WhatsApp o Telegram—,
email y programación automática.

## Disparador

Condición que hace que la fábrica cree un expediente o avance uno existente.
Puede ser una petición, un evento externo o una programación.

## Copiloto

Interfaz conversacional que ayuda a una persona a expresar una petición y la
convierte en una entrada estructurada para la fábrica. No sustituye las
políticas ni las aprobaciones del procedimiento.

## Petición

Intención expresada por una persona o sistema que puede dar lugar a un
expediente. Puede incluir texto, archivos, referencias y datos de contexto.

## Catálogo de procedimientos

Conjunto de procedimientos disponibles para una organización. El agente puede
proponer uno, pero no debe inventar procedimientos ni ejecutar uno ambiguo sin
confirmación.

## Política

Regla que limita qué puede hacer un procedimiento, quién puede aprobarlo y qué
severidad exige intervención humana.

## Rol

Responsabilidad de una persona dentro de una organización respecto a un
expediente o procedimiento: solicitante, operador, aprobador, propietario del
procedimiento o administrador.

## Subprocedimiento

Procedimiento reutilizable invocado por otro procedimiento. Comparte el
expediente principal y debe conservar sus propias entradas, resultado y
evidencia relacionada.

## Operación interna

Trabajo realizado para una organización sobre su propia información,
comunicaciones o sistemas, con independencia del departamento o proveedor
tecnológico implicado.

## Fuente de verdad

Sistema responsable de afirmar un tipo concreto de información. BACO es fuente
de verdad sobre sus expedientes y acciones; cada sistema externo conserva la
autoridad sobre sus propios datos.

## Adapter

Implementación que conecta un procedimiento o una capacidad del núcleo con una
herramienta concreta, sin exponer los detalles de esa herramienta al
procedimiento.

## Contrato de herramienta

Descripción común de lo que una herramienta recibe, devuelve, permite, rechaza,
registra y cómo identifica operaciones repetidas. MCP, una API o un comando
local pueden cumplir el mismo contrato.

## Versión activa

Versión de un procedimiento aprobada para nuevas ejecuciones. Los expedientes
existentes conservan la versión con la que comenzaron.

## Simulación

Ejecución que calcula y muestra las acciones previstas sin producir todavía sus
efectos externos.

## Línea temporal

Registro ordenado de los eventos de un expediente: entradas, decisiones,
aprobaciones, acciones, errores y resultados.

## Aprobación caducada

Aprobación que ya no autoriza una acción porque ha pasado su plazo o porque
cambió el estado, la evidencia o los datos revisados.
