# Skill: preparar campaña de artículos

## Propósito

Convertir una petición recibida desde cualquier canal y un Excel de artículos
en un borrador de campaña validado.

## Entrada

- `CampaignRequest`: asunto, audiencia, fecha opcional y origen de la petición.
- Ruta al archivo Excel de artículos.

## Procedimiento

1. Leer el Excel mediante el `ArticleReader` disponible.
2. Rechazar columnas ausentes, filas incompletas y hojas sin artículos.
3. Crear un `WorkItem` con la evidencia de la validación.
4. Guardar el trabajo como `awaiting_approval` cuando sea válido.
5. Detenerse antes de cualquier llamada a un proveedor de email.

## Regla de seguridad

Esta skill prepara; no envía. El envío de la campaña será otra skill y exigirá
una aprobación explícita y un `CampaignSender` concreto.
