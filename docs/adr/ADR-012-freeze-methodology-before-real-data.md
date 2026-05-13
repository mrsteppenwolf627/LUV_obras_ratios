# ADR-012: Congelación parcial metodológica antes del análisis de datos reales

**Estado:** PROPUESTA

## Contexto

Antes de analizar archivos reales, el proyecto necesita distinguir entre decisiones metodológicas ya seguras y decisiones que dependen de evidencia de datos.

## Decisión

Crear una revisión formal de ADR-009, ADR-010 y ADR-011 para identificar decisiones congelables y decisiones pendientes antes de iniciar el análisis controlado de archivos reales.

## Motivos

- Evitar pasar a parsers sin reglas mínimas.
- Evitar congelar decisiones que dependen de datos reales.
- Reducir riesgo de retrabajo.
- Mantener trazabilidad metodológica.
- Permitir que Fase 2 sea diagnóstico y no importación definitiva.

## Consecuencias

- El proyecto mantiene una puerta de control antes de analizar datos reales.
- Algunas decisiones quedan congeladas y otras permanecen abiertas.
- Fase 2 podrá ejecutarse con límites claros.
- No se podrá actualizar master real todavía.

## Documento relacionado

- `docs/decisions/human_review_phase_1_5.md`

## Estado de cambio

No congelar todavía hasta revisión humana.
