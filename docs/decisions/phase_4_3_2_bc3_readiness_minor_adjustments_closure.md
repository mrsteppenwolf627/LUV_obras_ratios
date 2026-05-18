# Fase 4.3.2: cierre de ajustes menores de readiness BC3

## 1. Objetivo

Cerrar de forma acotada los ajustes menores que mantienen el estado global en `VALIDATION_NEEDS_MINOR_ADJUSTMENTS`, sin ampliar capacidades generales del parser ni invadir fases fuera de alcance.

## 2. Estado de entrada

- Fase 4.3.1 implementada técnicamente.
- Estado real heredado:
  - `validation_metadata.status`: `WARNING`
  - `validation_readiness.global`: `VALIDATION_NEEDS_MINOR_ADJUSTMENTS`
- Readiness por archivo ya en `VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW`.

## 3. Causa exacta detectada

La causa del estado global no era un bloqueo real, sino clasificación:

- warnings heredados (`RELATION_CHILD_NOT_IN_CONCEPTS`, `ENCODING_MEDIUM_CONFIDENCE`, `MULTIPLE_UNITS_DETECTED`, `AMBIGUOUS_ECONOMIC_TOKENS`, `UNKNOWN_RECORD_TYPES_PRESENT`) se estaban acumulando como `minor_adjustment_items` por defecto;
- al existir cualquier `minor_adjustment_item`, la regla global priorizaba `VALIDATION_NEEDS_MINOR_ADJUSTMENTS`.

## 4. Clasificación aplicada en 4.3.2

1. Ajuste técnico corregible ahora:
- Reglas de clasificación de warnings heredados en `validate_bc3_intermediate.py`.

2. Warning no bloqueante:
- Relaciones huérfanas bajo umbral bloqueante.
- Señales de encoding medio.
- Unknown records preservados y no predominantes.
- Ambigüedad económica diagnóstica.

3. Decisión humana futura:
- `UNITS_POLICY_PENDING`.
- `ECONOMIC_POLICY_PENDING`.
- (sin decisión de categorías finales en esta fase).

4. Bloqueo real:
- Ninguno en el lote validado (sin `blocking_items`).

## 5. Cambios aplicados

- `scripts/validate_bc3_intermediate.py`:
  - se tipan como `non_blocking_manual_review` los warning codes no bloqueantes conocidos;
  - recomendación de readiness menor desacoplada de referencia textual a 4.3.1;
  - recomendación Markdown alineada para estado `MANUAL_REVIEW_REQUIRED` no bloqueante.

- `tests/scripts/test_validate_bc3_intermediate.py`:
  - nuevo test para verificar que warnings conocidos no se clasifican como `minor_adjustment_items`;
  - nuevo test de texto de recomendación en Markdown para manual review no bloqueante.

## 6. Resultado esperado de readiness

- Si no aparecen bloqueos reales: `VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW`.
- Si aparecieran bloqueos estructurales reales: `VALIDATION_BLOCKED`.
- En esta fase no se fuerza estado; se corrige clasificación.

## 7. Restricciones mantenidas

- No importación al master.
- No cálculo de ratios.
- No consolidación de importes.
- No normalización de categorías finales.
- No modificación de RAW.
- No subida de outputs reales sensibles.
