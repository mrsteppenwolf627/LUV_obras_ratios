# Fase 9.18 - clasificacion semantica de hojas XLSX y vistas profesionales adaptativas

## Objetivo de la fase

Eliminar la proyeccion forzada a una unica plantilla clasica y generar vistas profesionales adaptadas al tipo semantico real de cada hoja XLSX.

## Contexto desde Fase 9.17

- Fase 9.17 cerro el enforcement del pipeline oficial y el hard-stop post-generacion.
- Persistia una desviacion de producto: el pipeline seguia interpretando hojas heterogeneas como presupuesto clasico.
- Se mantiene `PREVIEW_ONLY`, sin promocion operativa, sin alimentacion de ratios y sin cambios en RAW.

## Problema de fondo detectado

- El pipeline mezclaba hojas con logicas diferentes en una unica vista `BUDGET_REVIEW_001`.
- Se inventaban jerarquias/subtotales sin evidencia explicita.
- En tablas comparativas, columnas semanticas se remapeaban mal (`Cap.` -> cantidad, `Importe equivalente` -> codigo).
- Filas de metadata/revision podian terminar como partidas economicas.

## Diagnostico previo obligatorio (auditoria de outputs existentes)

### Archivo sanitizado `REAL_XLSX_GENERALIZATION_001`

- Hojas detectadas:
  - `PRES_001_001_Datos`: patron de resumen economico con codigo + descripcion + formula + importe.
  - `PRES_001_002_Espacios`: patron de desglose por espacios (`Codigo/Info/Resumen/Pres`).
- Desviacion confirmada antes del cambio: ambas hojas se proyectaban en una vista clasica comun.
- Fila de metadata localizada en preservada: `13 abril 2026` (no debe tratarse como partida ni importe).
- Formulas con nombres definidos detectadas en preservada (`=D*/PEM`, etc.): deben mantenerse en capa preservada y no contaminar descripcion profesional.

### Archivo sanitizado `REAL_XLSX_GENERALIZATION_002`

- Cabeceras detectadas en preservada:
  - `Cap.`
  - `Nombre del capítulo`
  - `Importe (€)`
  - `Nombre equivalente`
  - `Importe equivalente`
  - `Diferencia`
- Diagnostico: la hoja es `COMPARISON_TABLE`, no presupuesto clasico de partidas.
- Regla aplicada: `Cap.` no puede mapearse a `Cantidad`, `Importe equivalente` no puede mapearse a `Codigo`, `Diferencia` no debe perderse.

## Tipos semanticos de hoja definidos

- `BUDGET_CLASSIC`
- `BUDGET_SUMMARY`
- `SPACE_BREAKDOWN`
- `COMPARISON_TABLE`
- `FORMULA_CALCULATION_SHEET`
- `AUXILIARY_SHEET`
- `METADATA_SHEET`
- `UNKNOWN`

## Reglas de clasificacion

- Deteccion por cabecera normalizada (tildes/caso/simbolos/saltos de linea).
- Fallback por patron estructural cuando no hay cabecera fiable.
- Densidad de formulas para detectar hojas de calculo auxiliar.
- Baja confianza -> advertencia `MANUAL_REVIEW_REQUIRED`.

## Vistas profesionales por tipo

- `BUDGET_CLASSIC`: `Codigo | Descripcion | Ud | Cantidad | Precio unitario | Importe`
- `BUDGET_SUMMARY`: `Codigo | Descripcion | Formula / Ratio | Importe`
- `SPACE_BREAKDOWN`: `Codigo | Info | Resumen | Presupuesto`
- `COMPARISON_TABLE`: `Cap. | Nombre del capítulo | Importe (€) | Nombre equivalente | Importe equivalente | Diferencia`
- `FORMULA_CALCULATION_SHEET`: `Concepto | Formula | Valor`
- `AUXILIARY_SHEET` / `METADATA_SHEET` / `UNKNOWN`: vista controlada + `MANUAL_REVIEW_REQUIRED`

## Reglas para no mezclar hojas

- `BUDGET_REVIEW_001` pasa a ser hoja HOME de navegacion semantica.
- Cada hoja origen relevante genera su propia vista profesional:
  - `BUDGET_REVIEW_001_<origen_sanitizado>`
- Se elimina la fusion de hojas heterogeneas en una tabla clasica unica.

## Reglas para no inventar cantidades/subtotales

- No se generan subtotales en `SPACE_BREAKDOWN` ni en `COMPARISON_TABLE`.
- No se rellena `Cantidad/Ud/Precio unitario` cuando no existe evidencia en hoja origen.
- Filas metadata (`revision/fecha + año`) se excluyen de vistas economicas.

## Reglas para tablas comparativas

- Se conserva la semantica comparativa completa incluyendo `Diferencia`.
- Se bloquea proyeccion de columnas clasicas (`Ud/Cantidad/Precio unitario`) en vistas comparativas.
- `Cap.` queda como `Cap.`, no como `Cantidad`.
- `Importe equivalente` queda como `Importe equivalente`, no como `Codigo`.

## Reglas para hojas de espacios

- Vista separada `Codigo | Info | Resumen | Presupuesto`.
- Sin mezcla con resumen economico.
- Sin subtotales generados por inferencia debil.

## Reglas para hojas de calculo/formula

- Identificacion por densidad de formulas y señales auxiliares.
- No conversion automatica a `COST_ITEMS` reales.
- Si no hay interpretacion fiable: `MANUAL_REVIEW_REQUIRED`.

## Cambios tecnicos realizados

- Nuevo modulo `scripts/xlsx_sheet_semantic_classifier.py`.
- Pipeline de extraccion actualizado para usar clasificacion por hoja antes de mapear.
- `scripts/live_excel_professional_output.py` reescrito para generar:
  - `BUDGET_REVIEW_001` (HOME)
  - vistas adaptativas por hoja origen
  - `BUDGET_REVIEW_TRACE_001` separado
- `scripts/generate_live_excel_master.py` actualizado:
  - fase de pipeline `9.18`
  - extraccion semantica no clasica (comparativas/espacios)
  - validacion post-generacion ampliada para reglas semanticas

## Validacion post-generacion ampliada

- Requiere HOME + vistas adaptativas + TRACE.
- Bloquea mezcla semantica.
- Bloquea comparativas con columnas clasicas inventadas.
- Bloquea metadata como partida economica.
- Bloquea `#NAME?`, formulas auxiliares en descripcion y columnas tecnicas visibles indebidas.
- Bloquea `COST_ITEMS` originados en hojas comparativas.

## Tests añadidos o modificados

- Nuevo: `tests/scripts/test_xlsx_sheet_semantic_classifier.py`
- Nuevo: `tests/scripts/test_xlsx_adaptive_professional_reviews.py`
- Actualizados:
  - `tests/scripts/test_live_excel_professional_output.py`
  - `tests/scripts/test_xlsx_output_pipeline_audit.py`
  - `tests/scripts/test_budget_review_semantic_correction.py`
  - `tests/scripts/test_live_excel_workbook_formatting.py`
  - `tests/scripts/test_xlsx_generalization_support.py`

## Resultado de regeneracion local 001/002

- Regeneracion ejecutada por ruta oficial:
  - `python scripts/run_xlsx_generalization_dry_run.py --files data/samples/<sanitized_001>.xlsx data/samples/<sanitized_002>.xlsx --output-dir outputs/live_excel_master/xlsx_generalization --report-json outputs/live_excel_master/xlsx_generalization/phase_9_18_report_sanitized.json`
- Validacion post-generacion:
  - `validate_generated_xlsx_preview(...)` -> `passed` para `001` y `002`.

### Resultado `REAL_XLSX_GENERALIZATION_001`

- HOME:
  - `Datos` -> `BUDGET_SUMMARY` -> `BUDGET_REVIEW_001_Datos`
  - `Espacios` -> `SPACE_BREAKDOWN` -> `BUDGET_REVIEW_001_Espacios`
- Confirmaciones:
  - no mezcla `Datos/Espacios` en una unica tabla clasica;
  - sin subtotales inventados en ambas vistas;
  - fila de revision/fecha (`abril 2026`) excluida de vista economica profesional;
  - formulas auxiliares fuera de `COST_ITEMS` reales.

### Resultado `REAL_XLSX_GENERALIZATION_002`

- HOME:
  - `Hoja1` -> `COMPARISON_TABLE` -> `BUDGET_REVIEW_001_Hoja1`
- Vista comparativa conservada:
  - `Cap.`
  - `Nombre del capítulo`
  - `Importe (€)`
  - `Nombre equivalente`
  - `Importe equivalente`
  - `Diferencia`
- Confirmaciones:
  - `Cap.` no se proyecta como `Cantidad`;
  - `Importe equivalente` no se proyecta como `Codigo`;
  - `Diferencia` conservada (formula/valor trazable);
  - no se generan columnas clasicas `Ud/Cantidad/Precio unitario`.

## Limitaciones

- La clasificacion semantica sigue siendo heuristica; puede requerir ajuste en layouts extremos.
- `UNKNOWN` y `AUXILIARY_SHEET` requieren revision manual antes de cualquier uso operativo.

## Riesgos

- Cabeceras no estandar o totalmente ausentes pueden degradar confianza semantica.
- Hojas mixtas dentro de una misma pestaña pueden requerir segmentacion adicional en fases posteriores.

## Recomendacion para Fase 9.19

- Ampliar muestra real XLSX y cerrar no-regresion semantica.
- Solo considerar apertura BC3 preservado cuando la ruta XLSX adaptativa quede estable en casos heterogeneos.
