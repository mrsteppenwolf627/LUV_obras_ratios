# Fase 9.12: endurecimiento de extraccion economica XLSX y mapping preserved -> COST_ITEMS

## 1. Objetivo de la fase

Resolver el cuello de botella real detectado tras el piloto 9.10: mejorar separacion economica en `XLSX` heterogeneos y endurecer el mapping `preserved -> COST_ITEMS`, manteniendo todo en modo `PREVIEW_ONLY`/dry-run y sin promocion operativa.

## 2. Contexto desde Fase 9.11

Fase 9.11 cerro documentalmente los hallazgos post-piloto y priorizo Linea A (`XLSX` economico heterogeneo) y Linea B (mapping `preserved -> COST_ITEMS`) antes de abrir ruta `BC3` preservada.

## 3. Problema real detectado en Fase 9.10

- `REAL_DRY_RUN_001` era candidato operativo, pero con deteccion economica parcial.
- `REAL_DRY_RUN_003` quedaba bloqueado por `amount_mixed_in_description` e `insufficient_amount_separation`.
- La trazabilidad funcionaba (`traceability_rate = 1.0`), pero la extraccion economica dependia demasiado de cabeceras exactas.
- El mapping anterior trataba muchas filas preservadas no presupuestarias como `UNMAPPED`, sin distinguir cabeceras, vacios, totales o capitulos.

## 4. Diagnostico inicial antes de tocar logica

Diagnostico sanitizado sobre `REAL_DRY_RUN_003`:

- Cabecera economica real no situada en primera fila.
- Cabecera parcial detectada: patron equivalente a `capitulo` + `importe`.
- La columna `importe` estaba disponible, pero la columna descriptiva se interpretaba de forma ambigua.
- Una columna numerica previa a la descripcion fue usada como fallback de `item_description`.
- Resultado: filas con `amount` separado pero `item_description` numerico, provocando `amount_mixed_in_description`.
- Los importes aparecian en celdas numericas y/o texto numerico interpretable; el parser anterior no cubria suficientemente formatos europeos/US.
- No habia evidencia suficiente para inferir con seguridad todas las columnas de cantidad y precio unitario.
- Se observaron filas de cabecera, vacias/no presupuestarias y partidas mezcladas en la capa preservada.
- Causa principal: cabecera parcial/ambigua y fallback de descripcion demasiado simple.

## 5. Que se intenta mejorar exactamente

- Normalizar cabeceras con tildes, mayusculas, signos, saltos de linea y variantes.
- Detectar `importe`, `total`, `presupuesto`, `coste`, `PEM`, `precio unitario`, `medicion`, `cantidad`, `unidad`, `descripcion`, `concepto`, `codigo`, `ref`.
- Parsear importes con separadores europeos y US.
- Usar columnas textuales como descripcion antes que columnas numericas.
- Extraer importes claramente embebidos al final de una descripcion, marcando baja confianza.
- Clasificar filas preservadas antes de mapearlas.
- Separar `UNMAPPED` de `NOT_COST_ITEM`.

## 6. Fuera de alcance

- Promocion automatica al master operativo.
- Ingesta real operativa.
- Calculo de ratios finales.
- Normalizacion final de categorias.
- Consolidacion definitiva de importes.
- Ruta `BC3` preservada.
- Tratamiento nuevo de Presto/PZH.
- Modificacion de RAW.
- Subida de muestras reales, Excels generados o reports sensibles.
- Interfaz, dashboard o UX.

## 7. Cambios tecnicos realizados

- Nuevo modulo `scripts/xlsx_budget_detection.py`.
- `scripts/generate_live_excel_master.py` delega deteccion XLSX en el nuevo modulo.
- `scripts/live_excel_dry_run_evaluator.py` distingue nuevos estados de mapping y motivos diagnosticos.
- `PRESERVED_TO_COST_ITEMS_MAP` mantiene contrato de columnas, pero permite estados mas precisos.
- `COST_ITEMS` solo se genera para filas clasificadas como `COST_ITEM` con evidencia suficiente.

## 8. Heuristicas economicas anadidas o endurecidas

- Normalizacion de cabeceras con eliminacion de tildes, signos, saltos de linea y espacios redundantes.
- Scoring de fila de cabecera por densidad de terminos economicos.
- Deteccion de cabecera fuera de primera fila.
- Inferencia por contenido cuando falta una cabecera clara.
- Preferencia por columna textual para `item_description`.
- Tratamiento de `capitulo` como descripcion util cuando la hoja usa esa cabecera para lineas economicas.
- Reconocimiento de `PEM` como senal de importe.

## 9. Parser numerico

Se implemento parser para:

- `687.5`
- `687,5`
- `687,50`
- `1.234,56`
- `1 234,56`
- `1,234.56`
- `€ 1.234,56`
- `1.234,56 €`
- `(1.234,56)`
- `-1.234,56`

Reglas:

- Rechaza codigos de partida en contexto de codigo.
- Rechaza anos en contexto no economico.
- Devuelve texto numerico normalizado con punto decimal.
- Marca baja confianza cuando el contexto no es plenamente monetario.

## 10. Reglas de separacion descripcion / cantidad / precio / importe

- `item_description` se toma de columna descriptiva o textual, no de concatenacion de toda la fila.
- `amount`, `quantity`, `unit_price` y `unit` se pueblan solo con evidencia.
- Si la descripcion tiene un importe final claro, se extrae el importe y se marca `AMOUNT_EXTRACTED_FROM_DESCRIPTION_LOW_CONFIDENCE`.
- Si el importe queda mezclado y no se puede separar, se marca `DESCRIPTION_AMOUNT_SPLIT_FAILED`.
- Se mantienen `source_sheet_name`, `source_row_number` y `preview_only=TRUE`.

## 11. Clasificacion de filas

Estados implementados:

- `CHAPTER`
- `SUBCHAPTER`
- `COST_ITEM`
- `SUBTOTAL`
- `TOTAL`
- `HEADER`
- `EMPTY`
- `NON_BUDGET_ROW`
- `UNKNOWN`
- `AMBIGUOUS`
- `MANUAL_REVIEW_REQUIRED`

Reglas principales:

- Cabeceras y filas vacias no se convierten en `COST_ITEMS`.
- Totales y subtotales no se convierten en `COST_ITEMS`.
- Filas con descripcion + importe/cantidad/precio/unidad se clasifican como `COST_ITEM`.
- Texto no presupuestario sin evidencia economica queda como `NON_BUDGET_ROW`.
- Ambiguedad economica queda como `AMBIGUOUS` o manual review, no como mapeo inventado.

## 12. Mejoras de mapping preserved -> COST_ITEMS

Estados soportados:

- `MAPPED`
- `UNMAPPED`
- `NOT_COST_ITEM`
- `AMBIGUOUS`
- `MANUAL_REVIEW_REQUIRED`

Metricas nuevas o endurecidas:

- `mapped_rows`
- `unmapped_rows`
- `not_cost_item_rows`
- `ambiguous_rows`
- `candidate_cost_item_rows`
- `mapping_rate_on_candidate_cost_items`

`mapping_rate` pasa a reflejar filas preservadas resueltas (`MAPPED` + `NOT_COST_ITEM`) sobre total preservado. Para lectura estricta de partidas reales se usa `mapping_rate_on_candidate_cost_items`.

## 13. Motivos nuevos del evaluador

- `economic_header_low_confidence`
- `numeric_parse_ambiguous`
- `description_amount_split_failed`
- `cost_item_mapping_ambiguous`
- `cost_item_mapping_low_confidence`

El evaluador sigue bloqueando si persiste importe mezclado en descripcion, separacion economica insuficiente, estados criticos, trazabilidad insuficiente o poblado indebido de ratios.

## 14. Tests anadidos o modificados

- Nuevo: `tests/scripts/test_xlsx_budget_detection.py`.
- Nuevo: `tests/scripts/test_live_excel_xlsx_economic_extraction.py`.
- Nuevo: `tests/scripts/test_live_excel_mapping_hardening.py`.
- Modificado: `tests/scripts/test_live_excel_budget_preservation.py`.

Cobertura:

- Cabeceras economicas heterogeneas.
- Parseo numerico europeo/US.
- Rechazo de codigos/anos fuera de contexto.
- Separacion descripcion/unidad/cantidad/precio/importe.
- Extraccion controlada de importe embebido al final de descripcion.
- Bloqueo si el importe sigue mezclado.
- Clasificacion de cabeceras, vacios, capitulos, totales, subtotales, partidas y ambiguos.
- Mapping `MAPPED`, `NOT_COST_ITEM` y `AMBIGUOUS`.
- Verificacion de que `RATIO_INPUTS` y `RATIOS_CALCULATED` no se alimentan.

## 15. Comparativa de metricas antes/despues sobre dry-run real

Comparativa con IDs sanitizados. Los outputs se generaron localmente bajo rutas ignoradas por Git.

| run_id | estado antes | estado despues | mapping_rate antes | mapping_rate despues | traceability antes | traceability despues | amount_sep antes | amount_sep despues | motivos antes | motivos despues |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| REAL_DRY_RUN_001 | OPERATIVE_CANDIDATE | OPERATIVE_CANDIDATE | 0.7938144329896907 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | ninguno | ninguno |
| REAL_DRY_RUN_002 | PROMOTION_BLOCKED | PROMOTION_BLOCKED | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | format_not_supported_for_preview_phase_9_10 | format_not_supported_for_preview_phase_9_10 |
| REAL_DRY_RUN_003 | PROMOTION_BLOCKED | OPERATIVE_CANDIDATE | 0.8048780487804879 | 1.0 | 1.0 | 1.0 | 0.0 | 1.0 | amount_mixed_in_description; insufficient_amount_separation | ninguno |

Nota tecnica: una repeticion aislada previa de baseline antes del cambio produjo `REAL_DRY_RUN_003 mapping_rate=0.9` al evitar acumulacion de previews antiguas; la tabla conserva como referencia de fase el valor documentado 9.10/9.11.

## 16. Resultado por archivo sanitizado

### REAL_DRY_RUN_001

- Formato: `XLSX`.
- Estado despues: `OPERATIVE_CANDIDATE`.
- No degrada estado.
- `traceability_rate = 1.0`.
- `amount_separation_rate = 1.0`.
- `mapping_rate_on_candidate_cost_items = 1.0`.
- Se identifican mas filas no presupuestarias como `NOT_COST_ITEM`, reduciendo ruido de `UNMAPPED`.

### REAL_DRY_RUN_002

- Formato: `BC3`.
- Estado despues: `PROMOTION_BLOCKED`.
- Motivo sin cambios: `format_not_supported_for_preview_phase_9_10`.
- No se aborda ruta `BC3` preservada en Fase 9.12.

### REAL_DRY_RUN_003

- Formato: `XLSX`.
- Estado antes: `PROMOTION_BLOCKED`.
- Estado despues: `OPERATIVE_CANDIDATE`.
- `amount_separation_rate`: `0.0 -> 1.0`.
- Desaparecen `amount_mixed_in_description` e `insufficient_amount_separation`.
- `RATIO_INPUTS` y `RATIOS_CALCULATED` permanecen vacios.

## 17. Limitaciones restantes

- Las heuristicas siguen siendo preliminares y deben validarse con mas layouts reales.
- Cantidad y precio unitario no se infieren si no hay evidencia suficiente.
- `mapping_rate` cambia de lectura al distinguir `NOT_COST_ITEM`; para partidas reales usar `mapping_rate_on_candidate_cost_items`.
- `BC3` preservado sigue pendiente.
- No hay normalizacion final ni categorias finales.

## 18. Riesgos

- Sobreajuste a pocos XLSX reales.
- Falsos positivos si una descripcion contiene numeros que no son importes.
- Layouts con formulas complejas o varias tablas por hoja pueden requerir una fase mayor.
- La mejora de mapping puede ocultar ruido si no se revisa la distribucion de `NOT_COST_ITEM`.

## 19. Recomendacion para Fase 9.13

Abrir Fase 9.13 como recalibracion post-endurecimiento con dos opciones:

1. Repetir prueba real ampliada de XLSX para validar que las heuristicas generalizan.
2. Si la muestra XLSX ampliada se mantiene estable, abrir la ruta `BC3` preservada en flujo 9.x.

No se recomienda promocion operativa todavia hasta validar con muestra mayor y mantener ratios vacios en preview.
