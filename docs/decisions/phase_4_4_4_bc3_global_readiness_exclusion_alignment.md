# Fase 4.4.4: alineación de readiness global con exclusión controlada

## 1. Objetivo

Ajustar de forma acotada la lógica de readiness global para permitir avance cuando los únicos casos problemáticos estén clasificados explícitamente como `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT` y exista subconjunto válido suficiente.

## 2. Contexto heredado

- Fase 4.4.2 introdujo tipificación de elegibilidad por archivo.
- Fase 4.4.3 desbloqueó `BC3_03` corrigiendo equivalencia `code`/`code#`.
- Queda un caso no apto (`BC3_02`) que debe permanecer visible como excluido controlado, no oculto.

## 3. Restricciones de fase

- No importación al master.
- No cálculo de ratios.
- No consolidación de importes.
- No normalización de categorías finales.
- No modificación de RAW.
- No subida de muestras reales ni reports reales sensibles.

## 4. Ajuste esperado

- Separar explícitamente exclusión controlada de bloqueo estructural.
- Mantener trazabilidad de archivos excluidos.
- Evitar estado global `ERROR` cuando no existan `BLOCKED_STRUCTURAL_ISSUE` y el subconjunto válido sea suficiente.

## 5. Campos de salida requeridos

- `excluded_files_count`
- `excluded_files_reason`
- `valid_subset_status`
- `full_corpus_status`
- `can_advance_with_valid_subset`
- `controlled_exclusions`

## 6. Criterio de readiness global

- Si existe al menos un `BLOCKED_STRUCTURAL_ISSUE`: mantener `VALIDATION_BLOCKED`.
- Si no existe bloqueo estructural y hay elegibles con exclusiones controladas: permitir avance con readiness no bloqueante.
- No ocultar archivos excluidos ni su motivo.

## 7. Evidencia de implementación y validación

- Script ajustado: `scripts/validate_bc3_intermediate.py`.
- Test suite ampliada: `tests/scripts/test_validate_bc3_intermediate.py`.
- Validaciones ejecutadas:
  - `python scripts/validate_context.py` OK
  - `python scripts/inspect_repo.py` OK
  - `pytest` OK (`72 passed`)
  - `python scripts/parse_bc3_preliminary.py` OK (5 BC3 detectados)
  - `python scripts/validate_bc3_intermediate.py` OK

Estado real resultante (lote local):

- `validation_metadata.status=MANUAL_REVIEW_REQUIRED`
- `validation_readiness.global=VALIDATION_READY_WITH_CONTROLLED_EXCLUSIONS`
- `full_corpus_status=NOT_BLOCKED`
- `valid_subset_status=ADVANCE_ALLOWED`
- `eligible_files_count=4`
- `excluded_files_count=1`
- `structurally_blocked_count=0`
- `controlled_exclusions=true`
- `can_advance_with_valid_subset=true`
- Exclusión explícita:
  - `BC3_02`: decode failure sin estructura útil (`~V/~C/~D`) y marcado como `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT`.

## 8. Recomendación final

Continuar con el subconjunto válido (`4` archivos elegibles) y mantener `BC3_02` fuera del flujo principal como exclusión controlada, sin ocultar su estado ni su motivo.
