# Fase 4.7: validación cruzada estricta de coherencia ~C/~D

## Objetivo

Implementar un validador estricto para la salida de `parse_bc3_strict.py`, centrado en coherencia estructural entre conceptos `~C` y relaciones `~D` en el subconjunto elegible.

## Entrada y salida

- Entrada: `reports/bc3_strict_parse/bc3_strict_parse_inventory.json`
- Salidas:
  - `reports/bc3_strict_validation/bc3_strict_validation_report.json`
  - `reports/bc3_strict_validation/bc3_strict_validation_report.md`

## Alcance

- Validación de raíz: `metadata`, `files`, `global_summary`.
- Validación por archivo elegible:
  - existencia de `~V`;
  - existencia de `~C`;
  - `~D` presente cuando aplica;
  - coherencia de relaciones con equivalencia `code/code#`;
  - orfandad parcial como `manual_review`;
  - orfandad masiva como bloqueo.
- Validación de excluidos:
  - visibles en `controlled_exclusions`;
  - no bloquean el subconjunto válido.

## Fuera de alcance

- Importación al master.
- Cálculo de ratios.
- Consolidación de importes.
- Normalización final de categorías/unidades.

## Estados y readiness

- Mantener en salida:
  - `full_corpus_status`
  - `valid_subset_status`
  - `validation_readiness`
- Regla global:
  - bloquea si hay bloqueo estructural en elegibles;
  - permite avance con exclusiones controladas cuando no hay bloqueos estructurales.

## Criterios de aceptación

- Validador estricto ejecutable sin parámetros o con input opcional.
- Reportes JSON/Markdown generados.
- Cobertura sintética mínima de coherencia `~C/~D` y exclusiones.
- Restricciones críticas preservadas.

## Riesgos

- Endurecer demasiado puede bloquear variantes válidas; se mitiga con umbrales explícitos y clasificación manual review frente a blocking.
- Dependencia de salida estricta previa; si el parse estricto cambia contrato, el validador debe ajustarse en fase siguiente.

## Siguientes pasos

1. Fase 4.8: reforzar casos sintéticos de variantes BC3/FIEBDC y calibrar umbrales si aparecen falsos bloqueos.
2. Definir contrato de integración entre validación estricta y futura capa de normalización (sin implementarla aún).
