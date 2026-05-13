# ADR-009: Diseño preliminar del master de ratios

**Estado:** PROPUESTA

## Contexto

El proyecto necesita una estructura de datos robusta antes de implementar parsers o app. Sin esta base, la evolución del sistema puede introducir pérdida de trazabilidad, errores de consolidación y cálculos no auditables.

## Decisión

Adoptar un master lógico por capas: RAW, proyectos, versiones, partidas, normalización, validación, inputs de ratio, ratios calculados, logs, fuentes y exclusiones.

## Motivos

- Evitar pérdida de datos.
- Permitir auditoría.
- Separar dato bruto de cálculo.
- Permitir validación antes de consolidación.
- Evitar ratios inventados.
- Soportar evolución progresiva.

## Consecuencias

- Mayor complejidad inicial.
- Mejor trazabilidad.
- Menor riesgo de errores.
- La app visual deberá respetar esta estructura.

## Estado de cambio

No congelar todavía hasta revisión humana.

## Documento relacionado

- `docs/decisions/master_schema_preliminar.md`
