# Fase 4.4.2: tipificación de aptitud de archivos BC3 y exclusión controlada

## 1. Objetivo

Incorporar tipificación explícita de aptitud por archivo BC3 para separar avance por subconjunto válido de bloqueo del corpus completo, sin ocultar riesgos estructurales.

## 2. Contexto heredado

- Fase 4.4 cerró con 5 BC3 analizados: 3 no bloqueantes y 2 bloqueados.
- Fase 4.4.1 clasificó los bloqueados:
  - `BC3_02`: no apto/auxiliar/corrupto (sin decodificación útil, sin estructura parseable).
  - `BC3_03`: bloqueado estructural por orfandad masiva (37/52, ratio 0.71).

## 3. Alcance técnico de 4.4.2

- Cambio acotado en `scripts/validate_bc3_intermediate.py` para añadir campos de elegibilidad por archivo y resumen global dual.
- Cobertura de tests sintéticos en `tests/scripts/test_validate_bc3_intermediate.py`.
- Sin cambios al parser preliminar.

## 4. Estados de elegibilidad definidos

- `ELIGIBLE_FOR_PRELIMINARY_FLOW`
- `ELIGIBLE_WITH_NON_BLOCKING_MANUAL_REVIEW`
- `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT`
- `BLOCKED_STRUCTURAL_ISSUE`

## 5. Reglas aplicadas

1. `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT`
- Archivo sin estructura útil de parse (sin `~V`, sin `~C`, sin `~D`) y con señal de decodificación fallida (`DECODE_FAILED`) o ausencia equivalente de estructura mínima.

2. `BLOCKED_STRUCTURAL_ISSUE`
- Archivo con bloqueadores estructurales de validación (por ejemplo `ORPHAN_RELATIONS_BLOCKING`, `MISSING_V_HEADER` con estructura no recuperable, `CONCEPTS_ABSENT_REVIEW` bloqueante real).

3. `ELIGIBLE_WITH_NON_BLOCKING_MANUAL_REVIEW`
- Archivo con warnings/manual review no bloqueantes, sin bloqueador estructural.

4. `ELIGIBLE_FOR_PRELIMINARY_FLOW`
- Archivo válido sin bloqueadores y sin manual review no bloqueante activo.

## 6. Campos nuevos por archivo

- `file_eligibility_status`
- `file_eligibility_reason`
- `can_advance_in_valid_subset`
- `blocks_full_corpus`
- `exclusion_recommendation`

## 7. Resumen global añadido

- `full_corpus_status`
- `valid_subset_status`
- `eligible_files_count`
- `excluded_or_not_eligible_count`
- `structurally_blocked_count`

Interpretación:

- `full_corpus_status=BLOCKED` si existe cualquier `BLOCKED_STRUCTURAL_ISSUE`.
- `valid_subset_status=ADVANCE_ALLOWED` si existe al menos un archivo elegible (`ELIGIBLE_*`) aunque el lote completo esté bloqueado.

## 8. Resultado esperado en corpus real actual

Con la evidencia previa de 4.4/4.4.1:

- `BC3_02` esperado como `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT`.
- `BC3_03` esperado como `BLOCKED_STRUCTURAL_ISSUE`.
- `BC3_01`, `BC3_04`, `BC3_05` esperados como `ELIGIBLE_WITH_NON_BLOCKING_MANUAL_REVIEW`.

## 9. Riesgos controlados

- Evitar “falso verde” global: el corpus completo sigue bloqueado cuando hay bloqueo estructural real.
- Evitar “falso rojo” operativo: se habilita avance técnico sobre subconjunto válido sin importar al master.

## 10. Recomendación final

- Continuar con validaciones/ajustes sobre subconjunto elegible.
- Mantener fuera del flujo principal los no aptos/auxiliares/corruptos.
- Tratar los bloqueados estructurales en fase acotada posterior con regresión sintética mínima.
