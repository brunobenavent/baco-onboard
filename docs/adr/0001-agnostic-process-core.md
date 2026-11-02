---
status: accepted
---

# Núcleo agnóstico de automatización de procesos

BACO Onboard tendrá un núcleo orientado a expedientes y procedimientos, no a
Mailchimp, Sage, albaranes ni a ningún proveedor concreto. Los canales de
entrada, las herramientas externas y MCP se conectarán mediante adapters que
cumplen contratos comunes; los procedimientos declararán políticas, severidad,
aprobaciones, simulación y evidencia. Elegimos esta separación para poder
automatizar operaciones internas de distintas organizaciones sin convertir el
primer caso de uso en el modelo de todo el sistema.

## Consecuencias

- Los expedientes conservarán la versión del procedimiento con la que comenzaron.
- Las acciones desconocidas o sin severidad quedarán bloqueadas.
- Los efectos externos tendrán simulación y una puerta de aprobación según la política.
- El primer proceso de campañas será un caso de prueba, no el centro del dominio.
