# Fase 9.9: evaluador dry-run combinado de promocion y preservacion

## Objetivo de la fase

Implementar un evaluador dry-run combinado por `run_id` que determine si una preview preservada puede considerarse candidata a futura ingesta operativa, sin promocion automatica.

## Contexto desde Fase 9.8

- Fase 9.8 dejo operativo el scaffolding de preservacion:
  - `PRESERVED_BUDGETS_INDEX`
  - `PRESERVED_BUDGET_SHEETS`
  - `PRESERVED_TO_COST_ITEMS_MAP`
  - hojas visibles `PRES_<budget_seq>_<sheet_seq>_<source_sanitized>`
- Faltaba combinar contrato de promocion (9.6) y preservacion (9.7) en una evaluacion unica.

## Alcance de implementacion

- Modulo dedicado: `scripts/live_excel_dry_run_evaluator.py`.
- Evaluacion no destructiva del workbook.
- Estados explicitos + motivos explicitos + metricas por evaluacion.
- Integracion opcional en CLI con `--evaluate-dry-run`.
- Tests sinteticos de estados clave.

## Fuera de alcance

- Promocion real automatica.
- Ingesta real operativa masiva.
- Calculo final de ratios.
- Normalizacion final de categorias.
- Interfaz/UX/dashboard.

## Contratos combinados

- Promocion 9.6: criterios PREVIEW_ONLY -> OPERATIVE (sin automatismo).
- Preservacion 9.7: coexistencia capa preservada + capa tecnica.
- Scaffolding 9.8: hojas indice/mapa y hojas preservadas visibles.

## Estados del evaluador

- `OPERATIVE_CANDIDATE`
- `PROMOTION_BLOCKED`
- `MANUAL_REVIEW_REQUIRED`
- `PRESERVATION_INCOMPLETE`

## Motivos de bloqueo implementados

- `blocked_validation_status`
- `error_validation_status`
- `unknown_validation_status`
- `broken_relationship`
- `duplicate_ids`
- `amount_mixed_in_description`
- `insufficient_amount_separation`
- `ratio_inputs_not_allowed`
- `ratios_calculated_not_allowed`

## Motivos de revision humana implementados

- `ambiguous_mapping`
- `manual_review_ratio_exceeded`

## Motivos de preservacion incompleta implementados

- `missing_preserved_sheet`
- `missing_preserved_budgets_index`
- `missing_preserved_budget_sheets`
- `missing_preserved_to_cost_item_mapping`
- `insufficient_traceability`

## Metricas calculadas

- `total_preview_rows`
- `total_preserved_rows`
- `mapped_rows`
- `unmapped_rows`
- `mapping_rate`
- `traceability_complete_rows`
- `traceability_rate`
- `manual_review_rows`
- `manual_review_rate`
- `blocked_rows`
- `blocked_rate`
- `amount_separated_rows`
- `amount_separation_rate`
- `ratio_input_rows`
- `ratio_calculated_rows`

## Umbrales usados (preliminares)

- `traceability_rate >= 0.95`
- `amount_separation_rate >= 0.85` (cuando aplica)
- `manual_review_rate <= 0.25`
- `blocked_rate = 0`

Estos umbrales se mantienen preliminares y deben recalibrarse con mas casos.

## Reporte por run_id

- El evaluador devuelve `run_id`, `state`, `reasons`, `metrics`, `thresholds` y `auto_promotion_enabled=false`.
- CLI opcional:
  - `python scripts/generate_live_excel_master.py --output <ruta_segura> --evaluate-dry-run --evaluate-run-id <run_id>`

## Como se evita promocion automatica

- El evaluador no escribe cambios operativos en el workbook.
- Siempre devuelve `auto_promotion_enabled=false`.
- El flujo solo diagnostica candidatura futura.

## Compatibilidad con Excel maestro vivo

- Mantiene `generate_live_excel_master.py` como CLI principal.
- Reutiliza validaciones de esquema/integridad existentes.
- No altera contratos previos 9.1-9.8.

## Tests anadidos o modificados

- Nuevo: `tests/scripts/test_live_excel_dry_run_evaluator.py`
- Cobertura minima:
  - candidato valido;
  - preservacion incompleta por falta de hojas/indices/mapa;
  - bloqueo por `BLOCKED`, estado desconocido y poblado indebido de `RATIO_INPUTS`;
  - revision manual por mapping ambiguo;
  - verificacion de no promocion automatica.

## Riesgos

- Posibles falsos positivos/negativos con layouts XLSX muy heterogeneos.
- Umbrales preliminares aun no calibrados con volumen amplio real.
- Deteccion de mezcla descripcion/importe simplificada en esta fase.

## Limitaciones

- No se evalua en 9.9 granularidad completa por celda (`source_column_number`) para todos los casos.
- No se decide promocion real; solo candidatura.

## Recomendacion para Fase 9.10

- Ejecutar piloto controlado de evaluaciones sobre mas casos reales aislados.
- Refinar umbrales preliminares con evidencia.
- Endurecer reglas de mapping ambiguo multi-hoja y trazabilidad por columna.
