# Fase 9.14 - Professional Budget Review Output

## Objetivo de la fase

Implementar una salida profesional de presupuesto para revision humana directa en el Excel maestro preview, manteniendo separada la capa tecnica de trazabilidad.

## Contexto desde Fase 9.13

- Fase 9.13 cerro validando generalizacion tecnica XLSX.
- La revision humana detecto que la salida era trazable pero no util como documento profesional.
- Se mantiene contrato PREVIEW_ONLY y bloqueo de promocion operativa.

## Problema detectado en revision humana

- `IMPORTED_BUDGET_VIEW` priorizaba columnas tecnicas y no parecia presupuesto profesional.
- Las hojas preservadas `PRES_*` eran correctas para auditoria, pero crudas para trabajo diario.
- Faltaba una hoja principal pensada para lectura de estudio con jerarquia y calculo revisable.

## Diferencia entre vistas

- Hoja tecnica: datos de pipeline (`IMPORTED_BUDGET_VIEW`, `COST_ITEMS`, `VALIDATION_RESULTS`).
- Hoja preservada cruda: copia visible de input con trazabilidad (`PRES_*`).
- Hoja profesional de revision: vista limpia para lectura humana con jerarquia, estilos y formulas (`BUDGET_REVIEW_*`).

## Definicion de "identico a un presupuesto real"

En esta fase significa:

- orden de lectura por capitulos y partidas;
- columnas profesionales (`Codigo`, `Descripcion`, `Ud`, `Cantidad`, `Precio unitario`, `Importe`);
- subtotales por capitulo y total general con formula cuando hay evidencia;
- formatos numericos/monetarios, anchos y alineaciones legibles;
- trazabilidad separada sin contaminar la hoja principal.

## Requisitos visuales implementados

- Titulo y metadata de modo (`PREVIEW_ONLY`) en cabecera.
- Cabecera de tabla en negrita y color neutro.
- Congelacion de paneles bajo cabecera (`A5`).
- Filtro en cabecera (`A4:F4`).
- Anchos de columna ajustados para lectura.
- Alineacion: texto izquierda, unidad centrada, numericos derecha.
- Estilo diferencial para `CHAPTER`, `SUBTOTAL`, `TOTAL`, `AMBIGUOUS`.
- Columna tecnica oculta `_review_row_id` para enlace interno de trazabilidad.

## Requisitos de logica interna Excel implementados

- `Importe = Cantidad * Precio unitario` cuando ambos campos existen.
- Si solo existe importe original, se conserva valor (sin inventar formula).
- Subtotal por capitulo generado como `SUM(...)` de partidas del bloque.
- Total general generado como `SUM(...)` de subtotales (o partidas si no hay subtotales).
- Si el input ya trae fila `TOTAL`, no se duplica un segundo total.

## Requisitos de formulas

- Formulas solo dentro de la hoja profesional.
- Sin dependencias a hojas tecnicas para calculos principales.
- Si no hay evidencia numerica suficiente, se conserva valor original.

## Requisitos de trazabilidad separada

- Nueva hoja `BUDGET_REVIEW_TRACE_*` conectada por `review_row_id`.
- Cada fila visible del presupuesto tiene entrada de trazabilidad.
- La traza conserva:
  - `source_file_id`, `import_batch_id`, `budget_version_id`;
  - `source_sheet_name`, `source_row_number`;
  - `preserved_row_id`, `cost_item_id`, `mapping_status`;
  - notas tecnicas agregadas.

## Hojas nuevas anadidas o modificadas

- Nueva: `BUDGET_REVIEW_001` (o secuencia incremental).
- Nueva: `BUDGET_REVIEW_TRACE_001` (o secuencia incremental).
- Sin eliminar ni sustituir:
  - `PRESERVED_BUDGETS_INDEX`
  - `PRESERVED_BUDGET_SHEETS`
  - `PRESERVED_TO_COST_ITEMS_MAP`
  - `IMPORTED_BUDGET_VIEW`
  - `COST_ITEMS`
  - `VALIDATION_RESULTS`

## Estrategia de estilos

- Paleta neutra, sin colores agresivos.
- Filas de capitulo con enfasis verde suave.
- Subtotales con enfasis naranja suave.
- Total general con enfasis gris.
- Filas ambiguas en amarillo suave.

## Estrategia de agrupacion por capitulos

- Uso de `row_class` ya calculada (`CHAPTER`, `COST_ITEM`, etc.).
- Partidas se mantienen en orden de extraccion.
- En cambio de capitulo se inserta subtotal calculado del bloque previo.

## Estrategia de subtotales y totales

- Subtotales auto-generados cuando el bloque de capitulo contiene partidas.
- Total general al final cuando no existe `TOTAL` en input.
- Si existe `TOTAL` en input, se reutiliza esa fila con formula agregada cuando procede.

## Estrategia de ocultacion/separacion de columnas tecnicas

- Hoja profesional sin columnas tecnicas visibles.
- `_review_row_id` oculto en columna `G`.
- Trazabilidad detallada movida a `BUDGET_REVIEW_TRACE_*`.

## Cambios tecnicos realizados

- Nuevo modulo: `scripts/live_excel_professional_output.py`.
- Integracion en `generate_preview_from_real_xlsx` (`scripts/generate_live_excel_master.py`):
  - construccion de hoja profesional;
  - construccion de hoja de traza;
  - registro en `CHANGELOG`.

## Tests anadidos o modificados

- Nuevo: `tests/scripts/test_live_excel_professional_output.py`.
- Cobertura:
  - creacion/orden de hojas profesionales;
  - cabecera limpia y ausencia de columnas tecnicas visibles;
  - estilos base (negrita, anchos, freeze panes, filtro);
  - formulas de partida/subtotales/total;
  - preservacion de importe original cuando falta cantidad/precio;
  - enlace de `review_row_id` con hoja de traza.

## Limitaciones

- No replica pixel-perfect de estilos del archivo original.
- No agrega hyperlinks internos (postergado por simplicidad operativa).
- Jerarquia depende de la calidad de `row_class` previa.
- No aborda BC3 en esta fase.

## Riesgos

- Algunos layouts XLSX extremos pueden requerir ajuste adicional de reglas visuales.
- Un `row_class` incorrecto puede afectar subtotalizacion en la vista profesional.
- Se necesita validacion humana continua para criterio de aceptacion de estudio.

## Recomendacion para Fase 9.15

1. Ejecutar ronda de validacion humana comparada sobre muestra real ampliada.
2. Ajustar reglas visuales/focales en casos ambiguos reales.
3. Definir checklist formal de "apto para trabajo de estudio".
4. Si el checklist se cumple de forma consistente, abrir decision de ruta BC3 preservada.
