# ADR-011: Política preliminar de validación matemática y consistencia

**Estado:** PROPUESTA

## Contexto

Antes de implementar parsers o analizar archivos reales, el sistema necesita reglas explícitas para decidir qué datos pueden conservarse, normalizarse, bloquearse, excluirse o alimentar ratios.

## Decisión

Adoptar una política preliminar de validación por severidad y por entidad, separando validaciones de archivo fuente, lote de importación, proyecto, superficie, versión de presupuesto, importes, partidas, categorías, duplicados, conflictos, elegibilidad para ratios y cálculo de ratios.

## Motivos

- Evitar ratios calculados con datos incompletos.
- Evitar importes inventados o estimados.
- Bloquear conflictos no resueltos.
- Separar importación RAW de elegibilidad para ratios.
- Hacer reproducible cada cálculo.
- Permitir revisión humana en casos ambiguos.

## Consecuencias

- Mayor complejidad antes de importar.
- Más estados intermedios.
- Menor riesgo de contaminación del master.
- Los parsers futuros deberán generar información suficiente para validar.
- Las tolerancias numéricas quedan pendientes de decisión humana.

## Documento relacionado

- `docs/decisions/validation_rules_policy.md`

## Estado de cambio

No congelar todavía hasta revisión humana.
