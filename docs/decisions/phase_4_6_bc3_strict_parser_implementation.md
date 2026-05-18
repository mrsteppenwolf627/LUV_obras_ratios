# Fase 4.6: implementación del parser BC3 estricto sobre subconjunto válido

## Objetivo

Implementar un parser BC3 estricto basado en Fase 4.5, limitado al subconjunto válido y manteniendo `BC3_02` excluido del flujo principal.

## Decisión de entrada

- Fase 4.5 cerrada documentalmente.
- Decisión humana vigente: avanzar con subconjunto válido y mantener `BC3_02` como `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT`.

## Alcance implementado

- Nuevo script `scripts/parse_bc3_strict.py`.
- Lectura no destructiva de BC3 desde `data/samples` a través del inventario preliminar.
- Cruce con elegibilidad por archivo desde `reports/bc3_intermediate_validation/bc3_intermediate_validation_report.json`.
- Parseo estricto de `~V`, `~C`, `~D` con trazabilidad de línea/registro.
- Separación explícita por archivo: `parsed`, `unknown`, `unsupported`, `errors`, `warnings`, `manual_review_required`.
- Exclusiones controladas explícitas para no aptos.
- Estado dual de lote: `full_corpus_status` y `valid_subset_status`.

## Fuera de alcance

- Importación al master.
- Cálculo de ratios.
- Consolidación de importes.
- Normalización final de categorías.
- Parser definitivo general para toda variante BC3/FIEBDC.

## Reglas de elegibilidad aplicadas

- `ELIGIBLE_FOR_PRELIMINARY_FLOW` y `ELIGIBLE_WITH_NON_BLOCKING_MANUAL_REVIEW`: entran en parseo estricto.
- `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT`: quedan en `controlled_exclusions`.
- `BLOCKED_STRUCTURAL_ISSUE`: bloquean corpus completo.

## Contrato de salida estricta

- JSON: `reports/bc3_strict_parse/bc3_strict_parse_inventory.json`
- Markdown: `reports/bc3_strict_parse/bc3_strict_parse_inventory_report.md`
- Estructura con:
  - `files[]` con parse estricto y trazabilidad;
  - `controlled_exclusions[]`;
  - `global_summary` con conteos de elegibles/excluidos/bloqueados y estados global/subconjunto.

## Criterios de aceptación

- Parser estricto operativo sin modificar inputs.
- Exclusión controlada visible de `BC3_02`.
- Subconjunto válido puede avanzar cuando no hay bloqueos estructurales.
- Cobertura de tests sintéticos para contrato estricto y restricciones de fase.

## Riesgos conocidos

- Variantes BC3 con estructuras no previstas pueden quedar en `unsupported` o `manual_review_required`.
- El parser estricto depende de la clasificación previa de elegibilidad del validador intermedio.

## Siguientes pasos

1. Fase 4.7: endurecer cobertura de variantes sintéticas nuevas detectadas.
2. Revisar si se requiere desacoplar aún más parse estricto y validación de elegibilidad para ejecución independiente.
