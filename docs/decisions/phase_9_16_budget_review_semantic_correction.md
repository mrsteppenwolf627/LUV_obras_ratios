# Fase 9.16 - correccion semantica de BUDGET_REVIEW_001 e INDEX

## Objetivo de la fase

Corregir errores funcionales visibles en la salida profesional:

- `BUDGET_REVIEW_001` no puede mezclar importes en `Descripcion`.
- `BUDGET_REVIEW_001` no puede dejar `Importe` vacio cuando el origen tiene importe claro.
- `INDEX` no puede mostrar ruido tecnico por formulas `HYPERLINK(...)`.
- Filas auxiliares/formulas internas no deben contaminar `COST_ITEMS` como partidas reales.

## Contexto desde Fase 9.15

- Fase 9.15 resolvio orden/estilo global del workbook.
- La revision humana confirmo que la estructura visual mejoro.
- Persistio una desviacion semantica: en ciertos XLSX reales, la hoja profesional no representaba correctamente la logica del presupuesto.

## Problema detectado por revision humana

En `outputs/live_excel_master/xlsx_generalization/xlsx_generalization_001_preview.xlsx`:

- `BUDGET_REVIEW_001` mostraba casos tipo:
  - `Codigo=LUV_AP`, `Descripcion=37297.09`, `Importe=vacio`.
- `INDEX` podia mostrar formulas `=HYPERLINK(...)` (origen del texto tecnico en algunos visores).
- Filas auxiliares de calculo interno aparecian en `COST_ITEMS` como `COST_ITEM` con `amount_raw=0`.

## Diagnostico tecnico de la confusion descripcion/importe

Diagnostico programatico (IDs sanitizados):

- Hoja de origen preservada equivalente (`PRES_001_001_Datos`) contiene filas con estructura valida:
  - columna de codigo (ej. `LUV_AP`);
  - columna de descripcion textual (ej. `EQUIPAMIENTO`);
  - columna de formula auxiliar (ej. `=D16 / PEM`);
  - columna de importe numerico (ej. `37297.09`).
- El detector previo podia seleccionar una fila de datos como pseudo-cabecera en confianza baja.
- En ese estado, el mapping podia interpretar la columna numerica como `item_description` y la columna de formula como `amount`.
- Resultado: `Descripcion` numerica y `Importe` vacio en vista profesional.

## Diagnostico tecnico del problema de INDEX/HYPERLINK

- `INDEX` se construia con formulas `=HYPERLINK(...)`.
- Algunos renderizadores muestran mensajes tecnicos sobre formulas no soportadas en lugar de navegacion limpia.
- Eso contamina la experiencia humana inicial del workbook.

## Diagnostico tecnico de errores #NAME?

- Filas auxiliares con formulas (`=PEM * ...`, `=HonPry * ...`) podian entrar como `COST_ITEM`.
- Si una formula textual pasa a una celda visible como formula, el visor puede mostrar `#NAME?`.
- Se requiere tratar formulas auxiliares como filas no partidas y/o texto seguro en vistas humanas.

## Reglas corregidas para construir BUDGET_REVIEW_001

- Prioridad semantica de descripcion:
  - si `item_description` es formula o numerico puro, intentar recuperar texto descriptivo real de la fila.
  - no usar importes numericos como descripcion cuando existe texto descriptivo.
- Recuperacion de importe:
  - si `amount` mapeado no es valido, recuperar desde patron numerico de fila con contexto economico.
  - si el valor numerico estaba en la columna mal tomada como descripcion, reaprovecharlo como importe.
- Recuperacion de codigo:
  - si `item_code` mapeado no parece codigo real (ej. importe decimal), recuperar codigo alternativo por patron de fila.

## Reglas corregidas para excluir filas auxiliares de COST_ITEMS

- Nuevas clases de fila:
  - `FORMULA_ROW`
  - `AUXILIARY_ROW`
  - `CALCULATION_ROW`
- Estas clases se mapean a `NOT_COST_ITEM`.
- Se excluyen de la extraccion operativa para que no generen `COST_ITEMS` espurios.
- Se mantiene compatibilidad con estados previos (`MAPPED`, `UNMAPPED`, `NOT_COST_ITEM`, `AMBIGUOUS`, `MANUAL_REVIEW_REQUIRED`).

## Cambios tecnicos realizados

- `scripts/xlsx_budget_detection.py`
  - endurecimiento del matching de cabeceras para evitar falsos positivos por subcadenas.
  - deteccion de texto tipo formula (`=...`) y clasificacion auxiliar/calculo.
  - recuperacion semantica de `Descripcion`, `Importe` y `Codigo` en casos de baja confianza.
  - exclusion de `FORMULA_ROW`/`AUXILIARY_ROW`/`CALCULATION_ROW` de la extraccion a capa operativa.
- `scripts/live_excel_workbook_formatting.py`
  - `INDEX` ahora usa texto limpio + `cell.hyperlink` interno (sin formula `=HYPERLINK(...)` visible).
- `scripts/live_excel_professional_output.py`
  - proteccion de texto en celdas de revision para no inyectar formulas visibles accidentalmente.

## Tests anadidos o modificados

- Nuevo: `tests/scripts/test_budget_review_semantic_correction.py`
  - valida semantica `Codigo/Descripcion/Importe` en caso sintetico equivalente al bug real.
  - valida que `INDEX` no use formulas `=HYPERLINK(...)` visibles ni texto tecnico.
  - valida que filas auxiliares de formula no entren en `COST_ITEMS` ni provoquen `#NAME?` en hoja profesional.

## Resultado de regeneracion local (sanitizado)

Regenerado local:

- `outputs/live_excel_master/xlsx_generalization/xlsx_generalization_001_preview.xlsx`

Verificado:

- Caso critico corregido en `BUDGET_REVIEW_001`:
  - `Codigo=LUV_AP`
  - `Descripcion=EQUIPAMIENTO`
  - `Importe=37297.09`
- `INDEX` sin textos tecnicos de formula.
- `BUDGET_REVIEW_001` sin `#NAME?` visible.
- Filas auxiliares de formula excluidas de `COST_ITEMS` como partidas.

## Limitaciones

- Persisten casos de baja confianza (`ECONOMIC_HEADER_LOW_CONFIDENCE`) en layouts muy irregulares.
- Parte de los codigos puede requerir ajuste adicional en hojas con estructura no tabular.

## Riesgos

- Heuristicas de recuperacion pueden sobreajustarse a ciertos patrones reales.
- Se requiere ampliar muestra real para confirmar estabilidad en todos los layouts XLSX heterogeneos.

## Recomendacion para Fase 9.17

- Consolidar precision semantica residual con muestra XLSX ampliada.
- Endurecer reglas de priorizacion de columnas cuando la cabecera sea ambigua.
- Mantener BC3 preservado fuera de activacion hasta cerrar no-regresion XLSX semantica.
