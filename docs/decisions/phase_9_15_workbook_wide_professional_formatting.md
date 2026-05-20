# Fase 9.15: profesionalizacion global del workbook y formato completo del Excel maestro

## Objetivo de la fase

Aplicar una capa de presentacion profesional a todo el workbook generado (no solo `BUDGET_REVIEW_001`) para que el documento completo sea navegable, legible y revisable por personas del estudio.

## Contexto desde Fase 9.14

- Fase 9.14 resolvio la primera hoja profesional (`BUDGET_REVIEW_*`) y su traza (`BUDGET_REVIEW_TRACE_*`).
- La revision humana confirmo que el resto del workbook seguia con aspecto tecnico crudo.
- Se mantiene el contrato `PREVIEW_ONLY`: sin promocion operativa, sin ratios finales, sin cambios en RAW.

## Problema detectado por revision humana

- Mejora local en primera hoja, pero calidad visual inconsistente en hojas preservadas/tecnicas.
- Falta de navegacion global y orden de lectura.
- Hojas vacias tecnicas se perciben como rotas en lugar de pendientes controladas.

## Clasificacion de hojas del workbook

### A. Hojas humanas principales

- `INDEX`
- `BUDGET_REVIEW_*`

### B. Hojas preservadas del input

- `PRES_*`
- `IMPORTED_BUDGET_VIEW`
- `PRESERVED_BUDGETS_INDEX`
- `PRESERVED_BUDGET_SHEETS`

### C. Hojas de trazabilidad

- `BUDGET_REVIEW_TRACE_*`
- `PRESERVED_TO_COST_ITEMS_MAP`
- `VALIDATION_RESULTS`

### D. Hojas tecnicas internas

- `SOURCE_FILES`, `IMPORT_LOG`, `BUDGET_VERSIONS`, `RAW_IMPORTS`, `COST_ITEMS`
- `NORMALIZED_COST_ITEMS`, `CATEGORY_MAPPING`, `RATIO_INPUTS`, `RATIOS_CALCULATED`
- `SNAPSHOTS`, `CHANGELOG`, `EXCLUSIONS`, `PROJECTS`, `README_MASTER`

## Reglas visuales por tipo de hoja

- Humanas: foco de lectura, sin gridlines, orientacion de impresion horizontal, estilo editorial limpio.
- Preservadas: formato tabular legible, conservando contenido/origen y ocultando trazas tecnicas intrusivas.
- Trazabilidad: tablas tecnicas claras (filtros, freeze panes, anchos y cabeceras fuertes).
- Tecnicas internas: tablas limpias, no decorativas, con legibilidad operativa y notas de estado cuando estan vacias.

## Reglas de orden de hojas

Orden aplicado por prioridad:

1. `INDEX`
2. `BUDGET_REVIEW_*`
3. `BUDGET_REVIEW_TRACE_*`
4. `PRES_*`
5. `IMPORTED_BUDGET_VIEW`
6. `PRESERVED_BUDGETS_INDEX`, `PRESERVED_BUDGET_SHEETS`
7. `PRESERVED_TO_COST_ITEMS_MAP`
8. `COST_ITEMS`
9. `VALIDATION_RESULTS`
10. Resto de tecnicas

## Reglas de visibilidad/ocultacion de hojas tecnicas

- No se elimina ninguna hoja tecnica obligatoria.
- Las hojas tecnicas se mueven al tramo final para no romper la experiencia de revision humana.
- Las columnas tecnicas en hojas humanas/preservadas no dominan la lectura; en `PRES_*` se ocultan prefijos `__source_*`.

## Reglas para hojas preservadas

- Se mantiene orden original de filas y columnas del input.
- Columnas de traza (`__source_*`) permanecen al final y ocultas.
- Se aplica estilo tabular profesional (cabecera, filtros, freeze panes, anchos).
- No se alteran valores originales ni formulas existentes.

## Reglas para hojas tecnicas

- Cabecera consistente (negrita, fondo suave, borde fino).
- Filtro + `freeze panes` en fila de cabecera.
- Ajuste de ancho de columnas.
- Para hojas tecnicas vacias de esta fase (`NORMALIZED_COST_ITEMS`, `CATEGORY_MAPPING`, `RATIO_INPUTS`, `RATIOS_CALCULATED`) se marca nota en comentario de cabecera: pendiente `PREVIEW_ONLY`.

## Reglas para hojas de trazabilidad

- `BUDGET_REVIEW_TRACE_*`, `PRESERVED_TO_COST_ITEMS_MAP` y `VALIDATION_RESULTS` quedan como tablas limpias y auditables.
- Se preserva enlace con filas visibles de `BUDGET_REVIEW_*` mediante `review_row_id`.

## Reglas para indice/navegacion

- Nueva hoja `INDEX` como puerta de entrada del workbook.
- Contiene:
  - descripcion del archivo;
  - modo `PREVIEW_ONLY`, no operativo y sin ratios finales;
  - instruccion: empezar por `BUDGET_REVIEW_001`;
  - advertencia de no editar hojas tecnicas manualmente;
  - listado de hojas con categoria y descripcion;
  - hyperlinks internos a cada hoja.

## Estrategia de estilos globales

- Fuente base `Calibri` tamano 10.
- Cabeceras en negrita con fondo neutro.
- Bordes finos en tablas.
- Freeze panes y autofilter en hojas tabulares.
- Anchos de columna auto-ajustados con limite superior.
- Tab colors por categoria (`INDEX`, `REVIEW`, `PRESERVED`, `TRACE`, `TECHNICAL`).

## Estrategia de page setup/impresion

- Hojas humanas (`BUDGET_REVIEW_*`): landscape, ajuste de ancho, titulos de impresion de cabecera.
- `INDEX`: gridlines ocultas para lectura limpia.
- Hojas tecnicas/preservadas: configuracion tabular estandar sin forzar diseno de impresion.

## Implementacion tecnica

- Nuevo modulo: `scripts/live_excel_workbook_formatting.py`.
- Funcion central: `apply_workbook_professional_formatting(workbook, mode_label="PREVIEW_ONLY")`.
- Integracion en `scripts/generate_live_excel_master.py` dentro de `generate_preview_from_real_xlsx(...)` despues de generar hoja profesional y antes de guardar.
- Registro en `CHANGELOG` de evento `workbook_professional_formatting`.

## Tests anadidos o modificados

- Nuevo: `tests/scripts/test_live_excel_workbook_formatting.py`
  - verifica `INDEX`, orden de hojas, modo `PREVIEW_ONLY`, posicion preferente de `BUDGET_REVIEW_*`;
  - valida formato de hojas `PRES_*` (columnas originales antes de tecnicas, trazas ocultas, freeze/filter);
  - valida formato de hojas tecnicas (`COST_ITEMS`, `VALIDATION_RESULTS`) y marca de pendientes en hojas vacias de ratios.
- Modificado: `tests/scripts/test_live_excel_professional_output.py`
  - ajustado a nuevo orden (`INDEX` primero, review/trace a continuacion).

## Evidencia local sanitizada (dry-run)

- Ejecucion local en `outputs/live_excel_master/xlsx_generalization/` con dos XLSX reales aislados disponibles.
- IDs sanitizados evaluados:
  - `REAL_XLSX_GENERALIZATION_001`
  - `REAL_XLSX_GENERALIZATION_002`
- Estado dry-run en ambos casos: `OPERATIVE_CANDIDATE`.
- Sin degradacion de seguridad:
  - `ratio_input_rows = 0.0`
  - `ratio_calculated_rows = 0.0`
  - sin promocion automatica
- Verificaciones visuales sobre cada preview:
  - `INDEX` en primera posicion.
  - `BUDGET_REVIEW_001` y `BUDGET_REVIEW_TRACE_001` al inicio.
  - `PRES_*` con columnas `__source_*` ocultas.
  - `COST_ITEMS`/`VALIDATION_RESULTS` con filtros y `freeze panes`.
  - hojas vacias de ratios marcadas como pendientes `PREVIEW_ONLY` por comentario.

## Limitaciones

- No se replica estilo pixel-perfect del XLSX origen (solo aproximacion profesional consistente).
- No se clona formato de celdas fusionadas complejas del input original.
- No se habilitan aun ocultaciones avanzadas por perfil de usuario.

## Riesgos

- Algunos layouts extremadamente irregulares pueden seguir requiriendo retoques de ancho/alineacion manual.
- Exceso de hojas tecnicas en escenarios futuros puede requerir un indice mas rico (secciones plegables o resumen adicional).

## Recomendacion para Fase 9.16

- Ejecutar aceptacion humana formal de workbook completo (no solo primera hoja) con checklist visual por tipo de hoja.
- Si aceptacion es positiva, abrir decision de ruta `BC3` preservada manteniendo el mismo estandar visual global.
- Si aceptacion detecta brechas, cerrar una iteracion de pulido estetico focalizada antes de BC3.
